"""
Conversation Manager orchestrating dialog state, guardrails,
information extraction, and tool execution.
"""

from datetime import datetime, timedelta, timezone
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from config.settings import settings
from backend.agent.state_manager import ConversationStateManager, ConversationState
from backend.agent.guardrails import evaluate_input_guardrails, verify_booking_hallucination
from backend.tools.clinical_tools import (
    get_clinic_information,
    get_doctor_information,
    check_availability,
    book_appointment,
    get_appointment,
    cancel_appointment,
    reschedule_appointment,
)

logger = logging.getLogger(__name__)


class ConversationManager:
    def __init__(self, session_id: str, db: Optional[Session] = None, now: Optional[datetime] = None):
        self.session_id = session_id
        self.state_mgr = ConversationStateManager(session_id)
        self.db = db
        self.now = now
        self.last_tool_call: Optional[Dict[str, Any]] = None
        self.last_tool_result: Optional[Dict[str, Any]] = None

    def extract_entities_rule_based(self, text: str) -> Dict[str, Any]:
        """
        Fast deterministic rule-based extractor for phone numbers, dates, times,
        doctor mentions, and names. Ideal for automated testing and fast fallback.
        """
        extracted: Dict[str, Any] = {}
        text_lower = text.lower()

        # 1. Intent Detection
        if any(w in text_lower for w in ["cancel", "call off"]):
            extracted["intent"] = "CANCEL_APPOINTMENT"
        elif any(w in text_lower for w in ["reschedule", "change my appointment", "move my appointment"]):
            extracted["intent"] = "RESCHEDULE_APPOINTMENT"
        elif any(w in text_lower for w in ["available", "free", "opening", "openings"]):
            extracted["intent"] = "CHECK_AVAILABILITY"
        elif any(w in text_lower for w in ["book", "schedule", "make an appointment", "see dr", "see doctor", "appointment"]):
            extracted["intent"] = "BOOK_APPOINTMENT"
        elif any(w in text_lower for w in ["hours", "address", "location", "clinic"]):
            extracted["intent"] = "CLINIC_INFORMATION"

        # 2. Doctor Matching
        if "ahmed" in text_lower or "khan" in text_lower:
            extracted["doctor_id"] = "DOC-001"
            extracted["doctor_name"] = "Dr. Ahmed Khan"
        elif "sarah" in text_lower or "patel" in text_lower or "derma" in text_lower:
            extracted["doctor_id"] = "DOC-002"
            extracted["doctor_name"] = "Dr. Sarah Patel"
        elif "michael" in text_lower or "chen" in text_lower or "cardio" in text_lower:
            extracted["doctor_id"] = "DOC-003"
            extracted["doctor_name"] = "Dr. Michael Chen"

        # 3. Phone Number Matching (e.g. 555-1234, (555) 123-4567, 5551234567)
        phone_match = re.search(r"(\+?\d{1,2}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}", text)
        if phone_match:
            extracted["contact_number"] = phone_match.group(0).strip()

        # 4. Date Normalization
        today = self.now or datetime.now(timezone.utc)
        if "tomorrow" in text_lower:
            extracted["appointment_date"] = (today + timedelta(days=1)).strftime("%Y-%m-%d")
        elif "today" in text_lower:
            extracted["appointment_date"] = today.strftime("%Y-%m-%d")
        else:
            # Check for YYYY-MM-DD
            iso_match = re.search(r"\b202\d-\d{2}-\d{2}\b", text)
            if iso_match:
                extracted["appointment_date"] = iso_match.group(0)

        # 5. Time Normalization (e.g. 10am, 10:30, 2 pm, 14:00)
        time_match = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", text_lower)
        if time_match:
            hr_str, min_str, period = time_match.groups()
            if period or min_str or (hr_str and int(hr_str) in range(8, 18)):
                hr = int(hr_str)
                minute = int(min_str) if min_str else 0
                if period == "pm" and hr < 12:
                    hr += 12
                elif period == "am" and hr == 12:
                    hr = 0
                # Filter reasonable daytime clinic hours (8 to 18)
                if 8 <= hr <= 18:
                    extracted["appointment_time"] = f"{hr:02d}:{minute:02d}"

        # 6. Patient Name Matching (e.g. "my name is Alice Smith", "this is Bob Jones", "I am Charlie Brown")
        name_match = re.search(r"(?:my name is|this is|i am|name's)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)", text, re.IGNORECASE)
        if name_match:
            extracted["patient_name"] = name_match.group(1).strip()
        correction_match = re.search(
            r"(?:wait\s*,?\s*sorry\s*,?\s*|actually\s*,?\s*)([A-Z][A-Za-z'-]*(?:\s+[A-Z][A-Za-z'-]*)?)",
            text,
        )
        if correction_match:
            extracted["patient_name"] = correction_match.group(1).strip()

        # 7. Appointment ID Matching (e.g. APT-12345678)
        apt_match = re.search(r"\b(APT-[A-Z0-9]{8})\b", text, re.IGNORECASE)
        if apt_match:
            extracted["appointment_id"] = apt_match.group(1).upper()

        # 8. Confirmation triggers
        if any(w in text_lower for w in ["yes", "confirm", "sure", "please do", "sounds good", "perfect", "book it"]):
            extracted["confirmed_by_patient"] = True

        return extracted

    def process_turn(self, user_utterance: str) -> str:
        """
        Executes one conversational turn:
        1. Checks input guardrails (emergency, diagnosis, privacy).
        2. Extracts entities and updates slots.
        3. Drives the state machine and executes verified tools.
        4. Validates final output against hallucinations.
        """
        # Step 1: Input Guardrails
        is_blocked, guardrail_response, category = evaluate_input_guardrails(user_utterance)
        if is_blocked and guardrail_response:
            if category == "EMERGENCY_ESCALATION":
                self.state_mgr.transition(ConversationState.EMERGENCY_ESCALATED, "Emergency detected")
            return guardrail_response

        # Step 2: Information Extraction & State Update
        extracted = self.extract_entities_rule_based(user_utterance)
        has_booking_request = any(
            phrase in user_utterance.lower()
            for phrase in ["book", "schedule", "make an appointment", "see dr", "see doctor"]
        )
        asks_clinic_info = any(
            phrase in user_utterance.lower() for phrase in ["hours", "address", "location", "where is your clinic"]
        )
        # A question such as "Can I book ...; where are you located?" is a
        # booking request with an interruption, not a replacement intent.
        if has_booking_request and extracted.get("intent") != "RESCHEDULE_APPOINTMENT":
            extracted["intent"] = "BOOK_APPOINTMENT"
        self.state_mgr.update_slots(extracted)

        slots = self.state_mgr.slots
        intent = slots.intent or "BOOK_APPOINTMENT"

        # Step 3: Handle Non-Booking Intents
        if intent == "CLINIC_INFORMATION":
            info = get_clinic_information()
            return f"{info['clinic_name']} is located at {info['address']}. We are open {info['operating_hours']}. How may I help you today?"

        if intent == "BOOK_APPOINTMENT" and asks_clinic_info:
            info = get_clinic_information()
            self.last_tool_call = {"tool": "get_clinic_information", "params": {}}
            self.last_tool_result = info
            if not self.state_mgr.is_booking_info_complete():
                question = self.state_mgr.get_next_question()
                return f"{info['clinic_name']} is located at {info['address']}. {question}"

        if intent == "CANCEL_APPOINTMENT":
            if not slots.appointment_id:
                return "I would be happy to help you cancel your appointment. Could you please provide your appointment confirmation number (starting with APT-)?"
            result = cancel_appointment(slots.appointment_id, db=self.db)
            self.state_mgr.transition(ConversationState.CANCELLED, "Appointment cancelled")
            return result.get("message", "Your appointment has been cancelled.")

        if intent == "RESCHEDULE_APPOINTMENT":
            if not slots.appointment_id:
                return "I can help reschedule your visit. Please provide your appointment confirmation number."
            if not slots.appointment_date:
                return "What new date would you prefer for the appointment?"
            if not slots.appointment_time:
                return "What new time would you prefer?"
            result = reschedule_appointment(
                appointment_id=slots.appointment_id,
                new_date=slots.appointment_date,
                new_time=slots.appointment_time,
                db=self.db,
            )
            self.last_tool_call = {
                "tool": "reschedule_appointment",
                "params": {"appointment_id": slots.appointment_id, "date": slots.appointment_date, "time": slots.appointment_time},
            }
            self.last_tool_result = result
            if result.get("status") == "CONFIRMED":
                self.state_mgr.transition(ConversationState.RESCHEDULED, "Appointment rescheduled")
            return result.get("message", "I could not reschedule that appointment.")

        # A caller may accept an offered alternative without repeating the time.
        # Select the first explicitly offered slot, then re-check it before any
        # confirmation or booking is possible.
        if self.state_mgr.state == ConversationState.OFFERING_ALTERNATIVES:
            accepted = extracted.get("confirmed_by_patient", False)
            if accepted and slots.available_alternatives:
                slots.appointment_time = slots.available_alternatives[0]
                slots.confirmed_by_patient = False
                self.state_mgr.transition(ConversationState.COLLECTING_INFO, "Alternative slot selected")
            elif accepted:
                return "I no longer have an available alternative to offer. What other date or time would you prefer?"

        # Step 4: Handle Appointment Booking Workflow
        # If required fields are incomplete, ask for the next missing field
        if not self.state_mgr.is_booking_info_complete():
            self.state_mgr.transition(ConversationState.COLLECTING_INFO, "Collecting missing booking fields")
            question = self.state_mgr.get_next_question()
            return question or "Could you please provide your appointment details?"

        # All 5 fields are present!
        # Step 5: Check Availability if not checked yet
        if self.state_mgr.state in [ConversationState.INIT, ConversationState.COLLECTING_INFO]:
            self.state_mgr.transition(ConversationState.CHECKING_AVAILABILITY, "Checking slot availability")
            doctor_id = slots.doctor_id or slots.doctor_name or "DOC-001"
            avail_result = check_availability(
                doctor_id=doctor_id,
                appointment_date=slots.appointment_date or "",
                preferred_time=slots.appointment_time,
                db=self.db,
            )
            self.last_tool_call = {"tool": "check_availability", "params": {"doctor_id": doctor_id, "date": slots.appointment_date, "time": slots.appointment_time}}
            self.last_tool_result = avail_result

            if avail_result.get("requested_time_available"):
                self.state_mgr.transition(ConversationState.CONFIRMING_DETAILS, "Slot available, awaiting confirmation")
                doc_name = avail_result.get("doctor_name", slots.doctor_name or "the doctor")
                return (
                    f"Great news! {doc_name} is available on {slots.appointment_date} at {slots.appointment_time} "
                    f"for {slots.patient_name}. Shall I go ahead and book this appointment for you?"
                )
            else:
                self.state_mgr.transition(ConversationState.OFFERING_ALTERNATIVES, "Slot busy, offering alternatives")
                alts = avail_result.get("alternative_slots", [])
                slots.available_alternatives = alts
                alt_str = ", ".join(alts[:2]) if alts else "another date"
                return (
                    f"I'm sorry, but {avail_result.get('doctor_name')} is not available at {slots.appointment_time} "
                    f"on {slots.appointment_date}. Some available times are {alt_str}. Would one of those work for you?"
                )

        # Step 6: Handle Confirmation / Booking Execution
        if self.state_mgr.state == ConversationState.CONFIRMING_DETAILS:
            if slots.confirmed_by_patient:
                self.state_mgr.transition(ConversationState.BOOKING, "Booking in progress")
                doctor_id = slots.doctor_id or "DOC-001"
                book_result = book_appointment(
                    patient_name=slots.patient_name or "Patient",
                    contact_number=slots.contact_number or "",
                    doctor_id=doctor_id,
                    appointment_date=slots.appointment_date or "",
                    appointment_time=slots.appointment_time or "",
                    idempotency_key=f"sess-{self.session_id}",
                    db=self.db,
                )
                self.last_tool_call = {"tool": "book_appointment", "params": {"patient_name": slots.patient_name, "doctor_id": doctor_id, "time": slots.appointment_time}}
                self.last_tool_result = book_result

                if book_result.get("status") == "CONFIRMED":
                    self.state_mgr.transition(ConversationState.BOOKED, "Appointment confirmed")
                    slots.appointment_id = book_result.get("appointment_id")
                    response = (
                        f"Your appointment is confirmed with {book_result.get('doctor_name')} "
                        f"on {slots.appointment_date} at {slots.appointment_time}. "
                        f"Your confirmation ID is {slots.appointment_id}. We look forward to seeing you!"
                    )
                    return verify_booking_hallucination(response, has_confirmed_booking=True)
                else:
                    return f"We ran into an issue while finalizing your booking: {book_result.get('message')}. Would you like to try another slot?"
            else:
                return (
                    f"Just to confirm, would you like me to book {slots.doctor_name or 'the doctor'} "
                    f"on {slots.appointment_date} at {slots.appointment_time} for {slots.patient_name}?"
                )

        # Fallback response
        return "How else may I assist you with your appointment today?"

