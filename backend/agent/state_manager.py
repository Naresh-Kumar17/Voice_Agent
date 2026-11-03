"""
Deterministic State Machine for Clinical Conversation Management.
Compliant with PRD Section 6.2 and Section 7.2.
Controls the dialogue progression, tracks slot collection, and prevents
unauthorized transitions.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class ConversationState(str, Enum):
    INIT = "INIT"
    IDENTIFY_INTENT = "IDENTIFY_INTENT"
    COLLECTING_INFO = "COLLECTING_INFO"
    CHECKING_AVAILABILITY = "CHECKING_AVAILABILITY"
    OFFERING_ALTERNATIVES = "OFFERING_ALTERNATIVES"
    CONFIRMING_DETAILS = "CONFIRMING_DETAILS"
    BOOKING = "BOOKING"
    BOOKED = "BOOKED"
    CANCELLED = "CANCELLED"
    RESCHEDULED = "RESCHEDULED"
    EMERGENCY_ESCALATED = "EMERGENCY_ESCALATED"
    CLOSING = "CLOSING"


class BookingSlots(BaseModel):
    intent: Optional[str] = None
    patient_name: Optional[str] = None
    contact_number: Optional[str] = None
    doctor_id: Optional[str] = None
    doctor_name: Optional[str] = None
    appointment_date: Optional[str] = None  # YYYY-MM-DD
    appointment_time: Optional[str] = None  # HH:MM
    appointment_type: str = "General Consultation"
    notes: Optional[str] = None
    appointment_id: Optional[str] = None
    confirmed_by_patient: bool = False
    available_alternatives: List[str] = Field(default_factory=list)


class ConversationStateManager:
    REQUIRED_BOOKING_FIELDS = [
        ("patient_name", "your full name"),
        ("contact_number", "the best phone number to reach you at"),
        ("doctor_name", "which doctor you would like to see"),
        ("appointment_date", "what date you are looking for"),
        ("appointment_time", "what time of day works best for you"),
    ]

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.state: ConversationState = ConversationState.INIT
        self.slots = BookingSlots()
        self.history: List[Dict[str, str]] = []
        self.state_history: List[ConversationState] = [ConversationState.INIT]

    def transition(self, new_state: ConversationState, reason: str = "") -> None:
        """Enforces and records a state transition."""
        self.state = new_state
        self.state_history.append(new_state)

    def update_slots(self, extracted: Dict[str, Any]) -> None:
        """Incrementally merges newly extracted slot values."""
        for field, value in extracted.items():
            if value is not None and hasattr(self.slots, field):
                # Clean strings
                if isinstance(value, str):
                    val_str = value.strip()
                    if val_str and val_str.lower() != "null":
                        setattr(self.slots, field, val_str)
                elif isinstance(value, (bool, list, int)):
                    setattr(self.slots, field, value)

    def get_missing_fields(self) -> List[Tuple[str, str]]:
        """Returns list of (field_name, prompt_description) for uncollected fields."""
        missing = []
        for field, desc in self.REQUIRED_BOOKING_FIELDS:
            val = getattr(self.slots, field)
            # For doctor, either doctor_id or doctor_name fulfills it
            if field == "doctor_name" and (self.slots.doctor_id or self.slots.doctor_name):
                continue
            if not val:
                missing.append((field, desc))
        return missing

    def is_booking_info_complete(self) -> bool:
        """Checks whether all 5 required fields are collected."""
        return len(self.get_missing_fields()) == 0

    def get_next_question(self) -> Optional[str]:
        """Generates a concise follow-up question for the next missing field."""
        missing = self.get_missing_fields()
        if not missing:
            return None
        next_field, desc = missing[0]
        if next_field == "patient_name":
            return "May I have your full name, please?"
        elif next_field == "contact_number":
            return "What is the best phone number to confirm your appointment?"
        elif next_field == "doctor_name":
            return "Do you have a specific doctor in mind, or are you looking for a general consultation?"
        elif next_field == "appointment_date":
            return "What date would you prefer for your visit?"
        elif next_field == "appointment_time":
            return "What time of day suits you best?"
        return f"Could you please share {desc}?"
