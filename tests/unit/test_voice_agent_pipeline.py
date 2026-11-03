"""
Unit tests for LiveKit Voice Agent pipeline instantiation, tool registration,
and multi-provider audio configuration.
"""

import pytest
from backend.agent import voice_agent
from backend.agent.voice_agent import (
    create_clinical_agent,
    build_llm,
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


def test_gemini_provider_configuration(monkeypatch):
    captured = {}
    expected = object()
    monkeypatch.setattr(voice_agent.settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(voice_agent.settings, "GEMINI_API_KEY", "local-test-key")
    monkeypatch.setattr(voice_agent.settings, "GEMINI_MODEL", "gemini-test-model")
    monkeypatch.setattr(
        voice_agent.openai,
        "LLM",
        lambda **kwargs: captured.update(kwargs) or expected,
    )

    assert build_llm() is expected
    assert captured["model"] == "gemini-test-model"
    assert captured["api_key"] == "local-test-key"
    assert captured["base_url"] == "https://generativelanguage.googleapis.com/v1beta/openai/"
    assert captured["extra_headers"]["x-goog-api-client"] == "clinical-voice-agent/1.0.0"


def test_gemini_provider_requires_key(monkeypatch):
    monkeypatch.setattr(voice_agent.settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(voice_agent.settings, "GEMINI_API_KEY", "")
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY is not configured"):
        build_llm()

