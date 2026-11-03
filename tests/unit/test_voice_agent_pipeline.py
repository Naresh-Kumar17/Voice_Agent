"""
Unit tests for LiveKit Voice Agent pipeline instantiation, tool registration,
and multi-provider audio configuration.
"""

import pytest
from backend.agent.voice_agent import (
    create_clinical_agent,
    CLINICAL_TOOLS,
    check_doctor_availability,
    book_clinical_appointment,
    lookup_doctor_information,
    lookup_clinic_information,
)


def test_agent_instantiation():
    agent = create_clinical_agent()
    assert agent is not None
    assert len(CLINICAL_TOOLS) == 6


def test_clinical_tools_callable():
    clinic_info = lookup_clinic_information()
    assert "Serenity Medical Clinic" in clinic_info

    doc_info = lookup_doctor_information(query="Ahmed")
    assert "Dr. Ahmed Khan" in doc_info


def test_tool_availability_execution():
    avail = check_doctor_availability(
        doctor_id="DOC-001",
        appointment_date="2026-11-04",
        preferred_time="10:00",
    )
    assert isinstance(avail, str)
    assert len(avail) > 0

