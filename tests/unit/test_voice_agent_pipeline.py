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
    lookup_existing_appointment,
    lookup_doctor_information,
    lookup_clinic_information,
)


def test_agent_instantiation():
    agent = create_clinical_agent()
    assert agent is not None
    assert len(CLINICAL_TOOLS) == 7


def test_agent_instructions_include_clinic_local_date(monkeypatch):
    class FixedDateTime:
        @classmethod
        def now(cls, tz):
            from datetime import datetime
            return datetime(2026, 11, 4, 9, 0, tzinfo=tz)

    monkeypatch.setattr(voice_agent, "datetime", FixedDateTime)
    instructions = voice_agent.build_receptionist_instructions()
    assert "Today's date is 2026-11-04 in the clinic timezone (America/New_York)." in instructions


@pytest.mark.asyncio
async def test_lookup_existing_appointment_returns_verified_date(monkeypatch):
    monkeypatch.setattr(
        voice_agent,
        "get_appointment",
        lambda appointment_id: {
            "found": True,
            "appointment_id": appointment_id,
            "doctor_name": "Dr. Ahmed Khan",
            "appointment_date": "2026-11-11",
            "start_time": "10:00",
            "status": "CONFIRMED",
        },
    )
    result = await lookup_existing_appointment(appointment_id="APT-12345678")
    assert "on 2026-11-11 at 10:00" in result
    assert "Status: CONFIRMED" in result


@pytest.mark.asyncio
async def test_clinical_tools_callable():
    clinic_info = await lookup_clinic_information()
    assert "Serenity Medical Clinic" in clinic_info

    doc_info = await lookup_doctor_information(query="Ahmed")
    assert "Dr. Ahmed Khan" in doc_info


@pytest.mark.asyncio
async def test_tool_availability_execution():
    avail = await check_doctor_availability(
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


def test_gemini_model_fallback_normalization(monkeypatch):
    captured = {}
    expected = object()
    monkeypatch.setattr(voice_agent.settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(voice_agent.settings, "GEMINI_API_KEY", "local-test-key")
    monkeypatch.setattr(voice_agent.settings, "GEMINI_MODEL", "gemini-3.8-flash")
    monkeypatch.setattr(
        voice_agent.openai,
        "LLM",
        lambda **kwargs: captured.update(kwargs) or expected,
    )

    assert build_llm() is expected
    # gemini-3.8-flash should automatically normalize to gemini-3.5-flash-lite
    assert captured["model"] == "gemini-3.5-flash-lite"


def test_elevenlabs_voice_fallback(monkeypatch):
    captured = {}
    expected = object()
    monkeypatch.setattr(voice_agent.settings, "TTS_PROVIDER", "elevenlabs")
    monkeypatch.setattr(voice_agent.settings, "ELEVENLABS_API_KEY", "sk-test-eleven")
    monkeypatch.setattr(voice_agent.settings, "ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
    monkeypatch.setattr(voice_agent.settings, "ELEVENLABS_MODEL_ID", "eleven_turbo_v2_5")

    class FakeElevenLabsTTS:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr("livekit.plugins.elevenlabs.TTS", FakeElevenLabsTTS)
    tts = voice_agent.build_tts()
    assert isinstance(tts, FakeElevenLabsTTS)
    # Rachel (21m00Tcm4TlvDq8ikWAM) should normalize to free premade voice Bella
    assert captured["voice_id"] == "EXAVITQu4vr4xnSDxMaL"


def test_elevenlabs_fallback_to_openai_without_key(monkeypatch):
    captured = {}
    expected = object()
    monkeypatch.setattr(voice_agent.settings, "TTS_PROVIDER", "elevenlabs")
    monkeypatch.setattr(voice_agent.settings, "ELEVENLABS_API_KEY", "")
    monkeypatch.setattr(voice_agent.openai, "TTS", lambda **kwargs: captured.update(kwargs) or expected)

    assert voice_agent.build_tts() is expected
    assert "voice" in captured


def test_deepgram_stt_fallback_without_key(monkeypatch):
    captured = {}
    expected = object()
    monkeypatch.setattr(voice_agent.settings, "STT_PROVIDER", "deepgram")
    monkeypatch.setattr(voice_agent.settings, "DEEPGRAM_API_KEY", "")
    monkeypatch.setattr(voice_agent.openai, "STT", lambda **kwargs: captured.update(kwargs) or expected)

    assert voice_agent.build_stt() is expected
    assert "api_key" in captured

