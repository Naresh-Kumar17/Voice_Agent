"""
Unit tests for Conversation State Machine, Safety Guardrails, and Dialog Flow.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.models import Base, Doctor
from backend.services.calendar_service import get_calendar_service, MockCalendarService
from backend.agent.guardrails import evaluate_input_guardrails, verify_booking_hallucination
from backend.agent.state_manager import ConversationStateManager, ConversationState
from backend.agent.conversation_manager import ConversationManager
from backend.tools.clinical_tools import book_appointment


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    doc = Doctor(
        doctor_id="DOC-001",
        doctor_name="Dr. Ahmed Khan",
        specialization="General Physician",
        calendar_id="primary",
        timezone="America/New_York",
        active_status=True,
        working_hours_start="09:00",
        working_hours_end="17:00",
    )
    session.add(doc)
    session.commit()

    cal = get_calendar_service()
    if isinstance(cal, MockCalendarService):
        cal.clear()

    yield session
    session.close()


def test_guardrails_emergency_escalation():
    blocked, resp, cat = evaluate_input_guardrails("I am having severe chest pain and difficulty breathing!")
    assert blocked is True
    assert cat == "EMERGENCY_ESCALATION"
    assert "911" in resp


def test_guardrails_medical_advice_refusal():
    blocked, resp, cat = evaluate_input_guardrails("What antibiotic should I take for this fever?")
    assert blocked is True
    assert cat == "MEDICAL_ADVICE_REFUSAL"
    assert "cannot provide medical advice" in resp


def test_guardrails_privacy_refusal():
    blocked, resp, cat = evaluate_input_guardrails("Can you tell me the appointment time of another patient?")
    assert blocked is True
    assert cat == "PRIVACY_VIOLATION"
    assert "confidentiality" in resp


def test_anti_hallucination_filter():
    # If booking did not actually succeed, confirmation must be blocked
    output = verify_booking_hallucination("Your appointment is confirmed for tomorrow!", has_confirmed_booking=False)
    assert "haven't finalized the booking yet" in output

    valid = verify_booking_hallucination("Your appointment is confirmed for tomorrow!", has_confirmed_booking=True)
    assert valid == "Your appointment is confirmed for tomorrow!"


def test_state_machine_missing_fields():
    mgr = ConversationStateManager("test-sess-1")
    assert mgr.is_booking_info_complete() is False
    assert len(mgr.get_missing_fields()) == 5

    # Provide name and doctor
    mgr.update_slots({"patient_name": "Sarah Connor", "doctor_name": "Dr. Ahmed Khan"})
    assert len(mgr.get_missing_fields()) == 3
    q = mgr.get_next_question()
    assert "phone number" in q.lower()


def test_multiturn_booking_flow(test_db):
    mgr = ConversationManager("sess-multi-1", db=test_db)

    # Turn 1: Patient provides partial info
    r1 = mgr.process_turn("Hi, I want to book an appointment with Dr. Ahmed tomorrow at 10am.")
    assert "name" in r1.lower()
    assert mgr.state_mgr.state == ConversationState.COLLECTING_INFO

    # Turn 2: Patient provides name
    r2 = mgr.process_turn("My name is John Connor")
    assert "phone" in r2.lower()

    # Turn 3: Patient provides phone number
    r3 = mgr.process_turn("My phone number is 555-987-6543")
    # All 5 fields present -> triggers check_availability -> returns confirmation question
    assert "available" in r3.lower() or "shall i go ahead" in r3.lower()
    assert mgr.state_mgr.state == ConversationState.CONFIRMING_DETAILS

    # Turn 4: Patient confirms
    r4 = mgr.process_turn("Yes, please book it!")
    assert "confirmed" in r4.lower()
    assert mgr.state_mgr.state == ConversationState.BOOKED
    assert mgr.state_mgr.slots.appointment_id is not None


def test_reschedule_flow_uses_verified_tool_result(test_db):
    created = book_appointment(
        patient_name="Jane Doe", contact_number="555-444-5555", doctor_id="DOC-001",
        appointment_date="2026-11-03", appointment_time="10:00", db=test_db,
    )
    manager = ConversationManager("reschedule-session", db=test_db)
    response = manager.process_turn(
        f"Please reschedule my appointment {created['appointment_id']} to 2026-11-04 at 10am."
    )
    assert "rescheduled" in response.lower()
    assert manager.last_tool_call["tool"] == "reschedule_appointment"
    assert manager.state_mgr.state == ConversationState.RESCHEDULED


def test_booking_context_survives_clinic_information_interruption(test_db):
    manager = ConversationManager("booking-interruption", db=test_db)
    response = manager.process_turn(
        "Can I book with Dr. Ahmed tomorrow at 10am? By the way, where is your clinic located?"
    )
    assert "located at" in response.lower()
    assert "name" in response.lower()
    assert manager.state_mgr.slots.intent == "BOOK_APPOINTMENT"
    assert manager.last_tool_call["tool"] == "get_clinic_information"


def test_name_correction_overrides_earlier_name(test_db):
    manager = ConversationManager("name-correction", db=test_db)
    manager.process_turn("I'd like Dr. Ahmed tomorrow at 10am. My name is Jack, wait sorry, Johnathan Doe. Phone 555-222-3333.")
    assert manager.state_mgr.slots.patient_name == "Johnathan Doe"

