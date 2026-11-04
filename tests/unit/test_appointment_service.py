"""
Unit tests for deterministic Clinical Appointment Service.
Verifies business logic, idempotency, collision prevention, and reconciliation.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.models import Base, Doctor
from backend.services.calendar_service import MockCalendarService
from backend.services.appointment_service import AppointmentService
from backend.api.schemas.appointment_schemas import AppointmentCreate


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed test doctor
    doc = Doctor(
        doctor_id="DOC-TEST-1",
        doctor_name="Dr. Test Physician",
        specialization="Family Medicine",
        calendar_id="primary",
        timezone="America/New_York",
        active_status=True,
        working_hours_start="09:00",
        working_hours_end="12:00",
    )
    session.add(doc)
    session.commit()

    yield session
    session.close()


@pytest.fixture
def mock_calendar():
    cal = MockCalendarService()
    cal.clear()
    return cal


def test_availability_calculation_empty(test_db, mock_calendar):
    service = AppointmentService(test_db, calendar_service=mock_calendar)
    res = service.check_availability("DOC-TEST-1", "2026-11-03", "09:00")
    assert res.requested_time_available is True
    assert "09:00" in res.available_slots
    assert "09:30" in res.available_slots
    assert "10:00" in res.available_slots


def test_availability_with_existing_calendar_event(test_db, mock_calendar):
    # Add busy event in calendar at 09:30
    mock_calendar.create_event(
        doctor_id="DOC-TEST-1",
        date_str="2026-11-03",
        start_time="09:30",
        end_time="10:00",
        summary="Busy",
    )

    service = AppointmentService(test_db, calendar_service=mock_calendar)
    res = service.check_availability("DOC-TEST-1", "2026-11-03", "09:30")
    assert res.requested_time_available is False
    assert "09:30" not in res.available_slots
    assert len(res.alternative_slots) > 0


def test_book_appointment_success(test_db, mock_calendar):
    service = AppointmentService(test_db, calendar_service=mock_calendar)
    req = AppointmentCreate(
        patient_name="Alice Smith",
        contact_number="555-1234",
        doctor_id="DOC-TEST-1",
        appointment_date="2026-11-03",
        appointment_time="10:00",
        idempotency_key="key-test-001",
    )
    resp = service.book_appointment(req)
    assert resp.status == "CONFIRMED"
    assert resp.patient_name == "Alice Smith"
    assert resp.start_time == "10:00"
    assert resp.calendar_event_id is not None
    event = mock_calendar.get_event("DOC-TEST-1", resp.calendar_event_id)
    assert (event["date"], event["start"], event["end"]) == ("2026-11-03", "10:00", "10:30")


def test_booking_rejects_calendar_event_that_does_not_match(test_db, mock_calendar, monkeypatch):
    original_get = mock_calendar.get_event

    def mismatched_event(doctor_id, event_id):
        event = original_get(doctor_id, event_id)
        if event:
            event["start"] = "11:00"
        return event

    monkeypatch.setattr(mock_calendar, "get_event", mismatched_event)
    service = AppointmentService(test_db, calendar_service=mock_calendar)
    req = AppointmentCreate(patient_name="A", contact_number="555", doctor_id="DOC-TEST-1",
                           appointment_date="2026-11-03", appointment_time="10:00")
    with pytest.raises(ConnectionError, match="verification failed"):
        service.book_appointment(req)
    assert mock_calendar.get_busy_intervals("DOC-TEST-1", "2026-11-03") == []


def test_book_appointment_idempotency(test_db, mock_calendar):
    service = AppointmentService(test_db, calendar_service=mock_calendar)
    req = AppointmentCreate(
        patient_name="Bob Jones",
        contact_number="555-5678",
        doctor_id="DOC-TEST-1",
        appointment_date="2026-11-03",
        appointment_time="10:30",
        idempotency_key="idempotent-key-123",
    )
    resp1 = service.book_appointment(req)
    # Retry with same idempotency key
    resp2 = service.book_appointment(req)
    assert resp1.appointment_id == resp2.appointment_id
    assert "idempotent" in resp2.message.lower()


def test_double_booking_prevention(test_db, mock_calendar):
    service = AppointmentService(test_db, calendar_service=mock_calendar)
    req1 = AppointmentCreate(
        patient_name="Caller One",
        contact_number="555-1111",
        doctor_id="DOC-TEST-1",
        appointment_date="2026-11-03",
        appointment_time="11:00",
    )
    service.book_appointment(req1)

    req2 = AppointmentCreate(
        patient_name="Caller Two",
        contact_number="555-2222",
        doctor_id="DOC-TEST-1",
        appointment_date="2026-11-03",
        appointment_time="11:00",
    )
    with pytest.raises(ValueError, match="already booked|not available"):
        service.book_appointment(req2)


def test_cancel_appointment(test_db, mock_calendar):
    service = AppointmentService(test_db, calendar_service=mock_calendar)
    req = AppointmentCreate(
        patient_name="Charlie Brown",
        contact_number="555-3333",
        doctor_id="DOC-TEST-1",
        appointment_date="2026-11-03",
        appointment_time="11:30",
    )
    created = service.book_appointment(req)
    cancelled = service.cancel_appointment(created.appointment_id)
    assert cancelled is True
    assert mock_calendar.get_event("DOC-TEST-1", created.calendar_event_id) is None

    # Check slot is now available again
    res = service.check_availability("DOC-TEST-1", "2026-11-03", "11:30")
    assert res.requested_time_available is True


def test_cancel_does_not_report_success_if_event_remains(test_db, mock_calendar, monkeypatch):
    service = AppointmentService(test_db, calendar_service=mock_calendar)
    req = AppointmentCreate(patient_name="Dana", contact_number="555", doctor_id="DOC-TEST-1",
                           appointment_date="2026-11-03", appointment_time="11:30")
    created = service.book_appointment(req)
    monkeypatch.setattr(mock_calendar, "delete_event", lambda *_: True)
    assert service.cancel_appointment(created.appointment_id) is False
    assert mock_calendar.get_event("DOC-TEST-1", created.calendar_event_id) is not None
    assert service.get_appointment(created.appointment_id).status == "CONFIRMED"


def test_reschedule_verifies_new_event_and_removes_old(test_db, mock_calendar):
    service = AppointmentService(test_db, calendar_service=mock_calendar)
    req = AppointmentCreate(patient_name="Eve", contact_number="555", doctor_id="DOC-TEST-1",
                           appointment_date="2026-11-03", appointment_time="09:00")
    created = service.book_appointment(req)
    updated = service.reschedule_appointment(created.appointment_id, "2026-11-04", "09:00")
    assert mock_calendar.get_event("DOC-TEST-1", created.calendar_event_id) is None
    new_event = mock_calendar.get_event("DOC-TEST-1", updated.calendar_event_id)
    assert (new_event["date"], new_event["start"], new_event["end"]) == ("2026-11-04", "09:00", "09:30")
