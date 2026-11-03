"""
Pydantic Schemas for Clinical Voice Agent API and Tool Contracts.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class PatientCreate(BaseModel):
    full_name: str = Field(..., description="Full name of the patient", min_length=2)
    phone_number: str = Field(..., description="Contact phone number", min_length=7)


class PatientResponse(BaseModel):
    patient_id: str
    full_name: str
    phone_number: str


class DoctorResponse(BaseModel):
    doctor_id: str
    doctor_name: str
    specialization: str
    calendar_id: str
    timezone: str
    active_status: bool
    working_hours_start: str
    working_hours_end: str


class TimeSlot(BaseModel):
    start_time: str = Field(..., description="Start time in HH:MM (24-hour) format")
    end_time: str = Field(..., description="End time in HH:MM (24-hour) format")
    is_available: bool = Field(True, description="Whether this slot is open")


class AvailabilityRequest(BaseModel):
    doctor_id: str = Field(..., description="ID of the doctor (e.g. DOC-001)")
    appointment_date: str = Field(..., description="Appointment date in YYYY-MM-DD format")
    preferred_time: Optional[str] = Field(None, description="Preferred time in HH:MM format")


class AvailabilityResponse(BaseModel):
    doctor_id: str
    doctor_name: str
    appointment_date: str
    requested_time_available: bool
    requested_time: Optional[str] = None
    available_slots: List[str] = Field(default_factory=list, description="List of available HH:MM slots")
    alternative_slots: List[str] = Field(default_factory=list, description="Alternative suggestions if requested time unavailable")
    message: str


class AppointmentCreate(BaseModel):
    patient_name: str = Field(..., description="Full patient name")
    contact_number: str = Field(..., description="Patient phone number")
    doctor_id: str = Field(..., description="Doctor ID (e.g. DOC-001)")
    appointment_date: str = Field(..., description="Date in YYYY-MM-DD format")
    appointment_time: str = Field(..., description="Start time in HH:MM format")
    appointment_type: str = Field("General Consultation", description="Reason or consultation type")
    idempotency_key: Optional[str] = Field(None, description="Unique key to avoid duplicate bookings")
    notes: Optional[str] = Field(None, description="Additional context or symptoms")


class AppointmentResponse(BaseModel):
    appointment_id: str
    patient_id: str
    patient_name: str
    contact_number: str
    doctor_id: str
    doctor_name: str
    appointment_date: str
    start_time: str
    end_time: str
    appointment_type: str
    status: str
    calendar_event_id: Optional[str] = None
    message: str


class AppointmentCancelRequest(BaseModel):
    appointment_id: str
    reason: Optional[str] = "Patient requested cancellation"


class ClinicInfoResponse(BaseModel):
    clinic_name: str
    phone: str
    address: str
    timezone: str
    opening_time: str
    closing_time: str
    appointment_duration_minutes: int

