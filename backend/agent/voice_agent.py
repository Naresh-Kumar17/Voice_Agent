"""
LiveKit Voice Agent Worker for Clinical Receptionist.
Configures the cascaded STT -> LLM -> TTS pipeline with real-time barge-in,
multi-provider support (Groq, OpenAI, Deepgram, ElevenLabs), and controlled tools.
Compliant with PRD Section 4, 5, 6, and 7.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure workspace root is on sys.path regardless of how script was invoked
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from dotenv import load_dotenv

# LiveKit's worker CLI reads credentials from process environment variables.
load_dotenv(override=False)

from livekit import rtc
from livekit.agents import (
    Agent,
    AgentSession,
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    function_tool,
)
from livekit.plugins import openai, silero

try:
    from livekit.plugins import deepgram
except ImportError:
    deepgram = None

try:
    from livekit.plugins import elevenlabs
except ImportError:
    elevenlabs = None

from config.settings import settings
from backend.agent.prompts import RECEPTIONIST_SYSTEM_PROMPT
from backend.tools.clinical_tools import (
    get_clinic_information,
    get_doctor_information,
    check_availability,
    book_appointment,
    get_appointment,
    cancel_appointment,
    reschedule_appointment,
)

logger = logging.getLogger("clinical_voice_agent")


# =====================================================================
# Provider Factories (Free-Tier Friendly & Pluggable)
# =====================================================================

def build_llm():
    """
    Constructs LLM provider.
    Defaults to Groq (ultra-low ~150ms TTFT, generous free tier) or OpenAI.
    """
    if settings.LLM_PROVIDER == "groq" and settings.GROQ_API_KEY:
        logger.info(f"Using Groq LLM: {settings.GROQ_MODEL}")
        return openai.LLM(
            model=settings.GROQ_MODEL,
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
            temperature=0.2,
        )
    if settings.LLM_PROVIDER == "gemini":
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("LLM_PROVIDER is gemini but GEMINI_API_KEY is not configured")
        model = settings.GEMINI_MODEL
        if model in ["gemini-3.8-flash", "gemini-2.5-flash", "gemini-2.0-flash"]:
            model = "gemini-3.1-flash-lite"
        logger.info(f"Using Gemini LLM: {model}")
        return openai.LLM(
            model=model,
            api_key=settings.GEMINI_API_KEY,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            temperature=0.2,
            extra_headers={"x-goog-api-client": "clinical-voice-agent/1.0.0"},
        )
    logger.info(f"Using OpenAI LLM: {settings.OPENAI_MODEL}")
    return openai.LLM(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY or "sk-dummy-key-for-test",
        temperature=0.2,
    )


def build_stt():
    """Constructs Speech-to-Text provider (Deepgram or OpenAI)."""
    if settings.STT_PROVIDER == "deepgram" and settings.DEEPGRAM_API_KEY and deepgram is not None:
        try:
            logger.info("Using Deepgram STT (nova-2-general)")
            return deepgram.STT(
                api_key=settings.DEEPGRAM_API_KEY,
                model="nova-2-general",
                language="en-US",
            )
        except Exception as e:
            logger.warning(f"Failed to load Deepgram plugin: {e}, falling back to OpenAI STT")
    api_key = settings.OPENAI_API_KEY or "sk-dummy-test-key-for-local-dev"
    return openai.STT(api_key=api_key)


def build_tts():
    """Constructs Text-to-Speech provider (ElevenLabs or OpenAI)."""
    if settings.TTS_PROVIDER == "elevenlabs" and settings.ELEVENLABS_API_KEY and elevenlabs is not None:
        try:
            voice_id = settings.ELEVENLABS_VOICE_ID
            # Rachel (21m00Tcm4TlvDq8ikWAM) requires a paid tier; EXAVITQu4vr4xnSDxMaL (Bella) is free premade
            if voice_id == "21m00Tcm4TlvDq8ikWAM":
                voice_id = "EXAVITQu4vr4xnSDxMaL"
            logger.info(f"Using ElevenLabs TTS (Voice: {voice_id})")
            return elevenlabs.TTS(
                api_key=settings.ELEVENLABS_API_KEY,
                voice_id=voice_id,
                model=settings.ELEVENLABS_MODEL_ID,
            )
        except Exception as e:
            logger.warning(f"Failed to load ElevenLabs plugin: {e}, falling back to OpenAI TTS")
    api_key = settings.OPENAI_API_KEY or "sk-dummy-test-key-for-local-dev"
    return openai.TTS(api_key=api_key, voice="alloy")


def build_vad():
    """Loads Silero Voice Activity Detector for barge-in and turn detection."""
    try:
        return silero.VAD.load()
    except Exception as e:
        logger.warning(f"Failed to load Silero VAD: {e}")
        return None


# =====================================================================
# LiveKit Function Tool Registrations
# =====================================================================

@function_tool
def check_doctor_availability(
    doctor_id: str,
    appointment_date: str,
    preferred_time: Optional[str] = None,
) -> str:
    """
    Check if a doctor is available on a specific date (YYYY-MM-DD) and optional time (HH:MM).
    Always call this tool before telling a patient that a slot is free.
    """
    res = check_availability(
        doctor_id=doctor_id,
        appointment_date=appointment_date,
        preferred_time=preferred_time,
    )
    return res.get("message", "Checked availability.")


@function_tool
def book_clinical_appointment(
    patient_name: str,
    contact_number: str,
    doctor_id: str,
    appointment_date: str,
    appointment_time: str,
    appointment_type: str = "General Consultation",
) -> str:
    """
    Confirm and book an appointment after the patient has explicitly agreed.
    Requires patient name, contact number, doctor ID/name, date (YYYY-MM-DD), and time (HH:MM).
    """
    res = book_appointment(
        patient_name=patient_name,
        contact_number=contact_number,
        doctor_id=doctor_id,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        appointment_type=appointment_type,
    )
    return res.get("message", "Appointment operation processed.")


@function_tool
def lookup_doctor_information(query: Optional[str] = None) -> str:
    """
    Retrieve doctors at the clinic and their medical specialties.
    Query can be a doctor's name or medical field (e.g. 'Dermatologist').
    """
    res = get_doctor_information(query=query)
    docs = res.get("doctors", [])
    if not docs:
        return "No doctors currently match that query."
    doc_lines = [f"{d['name']} ({d['specialization']}) - Hours: {d['working_hours']}" for d in docs]
    return "Our clinic doctors are: " + "; ".join(doc_lines)


@function_tool
def lookup_clinic_information() -> str:
    """
    Get general clinic administrative information including hours, address, and phone number.
    """
    info = get_clinic_information()
    return (
        f"{info['clinic_name']} is located at {info['address']}. "
        f"Phone: {info['phone']}. Hours: {info['operating_hours']}."
    )


@function_tool
def cancel_existing_appointment(appointment_id: str) -> str:
    """
    Cancel an appointment given its confirmation ID (e.g. APT-XXXXXX).
    """
    res = cancel_appointment(appointment_id=appointment_id)
    return res.get("message", "Cancellation processed.")


@function_tool
def reschedule_existing_appointment(
    appointment_id: str,
    new_date: str,
    new_time: str,
) -> str:
    """
    Reschedule an existing appointment to a new date (YYYY-MM-DD) and time (HH:MM).
    """
    res = reschedule_appointment(
        appointment_id=appointment_id,
        new_date=new_date,
        new_time=new_time,
    )
    return res.get("message", "Rescheduling processed.")


CLINICAL_TOOLS = [
    check_doctor_availability,
    book_clinical_appointment,
    lookup_doctor_information,
    lookup_clinic_information,
    cancel_existing_appointment,
    reschedule_existing_appointment,
]


# =====================================================================
# Clinical Agent Factory
# =====================================================================

def create_clinical_agent() -> Agent:
    """Factory to create a configured LiveKit Agent with tools and prompts."""
    instructions = RECEPTIONIST_SYSTEM_PROMPT.format(
        clinic_name=settings.CLINIC_NAME,
        clinic_phone=settings.CLINIC_PHONE,
        clinic_address=settings.CLINIC_ADDRESS,
        clinic_opening_time=settings.CLINIC_OPENING_TIME,
        clinic_closing_time=settings.CLINIC_CLOSING_TIME,
        clinic_timezone=settings.CLINIC_TIMEZONE,
    )

    llm = build_llm()
    stt = build_stt()
    tts = build_tts()
    vad = build_vad()

    return Agent(
        instructions=instructions,
        tools=CLINICAL_TOOLS,
        llm=llm,
        stt=stt,
        tts=tts,
        vad=vad,
        allow_interruptions=True,
    )


# =====================================================================
# LiveKit Worker Entrypoint
# =====================================================================

async def entrypoint(ctx: JobContext):
    """LiveKit agent worker lifecycle entry point."""
    logger.info(f"Connecting to room: {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait for the first human participant
    participant = await ctx.wait_for_participant()
    logger.info(f"Starting voice session with participant: {participant.identity}")

    agent = create_clinical_agent()
    session = AgentSession()
    await session.start(agent, room=ctx.room)

    # Greet patient immediately
    greeting = (
        f"Hello! Thank you for calling {settings.CLINIC_NAME}. "
        "I'm Rachel, your AI receptionist. How can I help you today?"
    )
    await session.say(greeting)


def main():
    """Runs the LiveKit worker CLI."""
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name=settings.LIVEKIT_AGENT_NAME,
        )
    )


if __name__ == "__main__":
    main()

