# Clinical Voice Agent — Project Context File
# Workspace: F:\Voice_Agent (git: main branch)
# Updated: 2026-11-03

## What Is This Project?

A **production-grade Clinical AI Receptionist ("Rachel")** — a real-time voice agent that:
- Answers patient calls using LiveKit WebRTC audio streaming.
- Transcribes patient speech with Deepgram Nova-2 (`nova-2-general`).
- Processes conversation turns with Google Gemini (`gemini-3.1-flash-lite` via OpenAI-compatible endpoint).
- Speaks back using ElevenLabs TTS (`eleven_turbo_v2_5` with free-tier premade voice `Bella` / `EXAVITQu4vr4xnSDxMaL`).
- Checks doctor availability against Google Calendar (sandbox / live).
- Books, reschedules, and cancels appointments deterministically with two-phase commit and audit logging.
- Enforces clinical safety guardrails (emergency 911 escalation, medical advice refusal, HIPAA patient privacy protection, anti-hallucination verification).
- Provides a modern React + TypeScript + Vite frontend with live WebRTC audio and an Autonomous Evaluation Dashboard.

---

## Current Architecture & Status Summary

| Area | Status | Evidence |
|---|---|---|
| **Phase 1: Foundation & Data Architecture** | ✅ COMPLETE | 8 SQLAlchemy models, repository pattern, Pydantic v2 schemas, SQLite/Postgres DB setup |
| **Phase 2: Controlled Agent Tools** | ✅ COMPLETE | 8 clinical tools (`get_clinic_information`, `get_doctor_information`, `check_availability`, `book_appointment`, `cancel_appointment`, `reschedule_appointment`, etc.) |
| **Phase 3: Conversation State & Guardrails** | ✅ COMPLETE | 12-state conversation manager, emergency 911 escalation, medical advice refusal, privacy filter, anti-hallucination validation |
| **Phase 4: LiveKit Voice Agent Pipeline** | ✅ COMPLETE | LiveKit Agents v1.8 worker, Gemini LLM fallback, Deepgram STT, ElevenLabs TTS free-tier fallback, Silero VAD |
| **Phase 5: Autonomous Evaluation Engine** | ✅ COMPLETE | 15 deterministic scenarios (TC-001–TC-029), simulated patient persona, ground-truth DB verifier, safety & tool evaluators |
| **Phase 6: FastAPI REST API & Token Service** | ✅ COMPLETE | FastAPI with CORS, appointment routes, LiveKit room token generator & named-agent dispatcher |
| **Phase 7: React Frontend & Evaluation Dashboard** | ✅ COMPLETE | React 19 + TypeScript + Vite, WebRTC voice call panel, audio visualizer orb, live transcript, scenario runner |
| **Phase 8: Docker & Production Runbook** | ✅ COMPLETE | Multi-stage Dockerfile, docker-compose.yml, nginx configuration, production runbook |

**Test Status**: **43 / 43 automated tests passing** across unit and integration suites.

---

## Root Cause Analysis: Server Testing "status : not found"

When testing the server or LiveKit Cloud console, `"status : not found"` occurred due to four distinct issues:

1. **LiveKit Cloud Worker Offline**:
   - LiveKit Cloud Console displays `Agent status: Not found` if no LiveKit agent worker process is actively connected to the project WebSocket (`wss://live-interview-267n30oe.livekit.cloud`) and registered under `agent_name = "clinical-voice-agent"`.
   - **Fix**: Launch the worker with `.venv\Scripts\python backend/agent/voice_agent.py dev` (or `start`). Once connected, the worker registers with LiveKit Cloud and receives dispatches immediately.

2. **Gemini Model Incompatibility (`gemini-3.8-flash`)**:
   - The user `.env` specified `GEMINI_MODEL=gemini-3.8-flash`.
   - On Google's OpenAI-compatible endpoint (`https://generativelanguage.googleapis.com/v1beta/openai/`), `gemini-3.8-flash` is not an active endpoint and returns HTTP 404 (`status: NOT_FOUND`) or HTTP 503 (`UNAVAILABLE`).
   - **Fix**: Added automatic model normalization in `backend/agent/voice_agent.py` to route to `gemini-3.1-flash-lite`, which is fully active and responds with ultra-low latency.

3. **ElevenLabs Free-Tier Voice Permission (HTTP 402)**:
   - The voice ID `21m00Tcm4TlvDq8ikWAM` ("Rachel") is a library voice that returns HTTP 402 `paid_plan_required: "Free users cannot use library voices via the API"` on free-tier ElevenLabs accounts.
   - **Fix**: Added automatic fallback in `backend/agent/voice_agent.py` to `EXAVITQu4vr4xnSDxMaL` ("Bella"), a free premade voice available on all ElevenLabs free-tier accounts.

4. **Worker CLI Python Path**:
   - Running `python backend/agent/voice_agent.py` failed with `ModuleNotFoundError: No module named 'config'` because `sys.path` did not contain the repository root when invoked directly.
   - **Fix**: Dynamically injected the repository root directory into `sys.path` in `backend/agent/voice_agent.py`.

---

## Complete Method to Run the System

To run the complete system locally with full voice calling and dashboard:

### Terminal 1: FastAPI REST API
```powershell
# Navigate to repository root
cd F:\Voice_Agent

# Activate virtual environment
.venv\Scripts\activate

# Launch API server
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be accessible at: `http://localhost:8000/docs`

### Terminal 2: LiveKit Voice Agent Worker
```powershell
# Navigate to repository root
cd F:\Voice_Agent

# Activate virtual environment
.venv\Scripts\activate

# Start the agent worker in development mode (hot reloading)
python backend/agent/voice_agent.py dev
```
You should see:
```text
Connecting to LiveKit server: wss://live-interview-267n30oe.livekit.cloud
Registered agent worker: clinical-voice-agent
```

### Terminal 3: React Web Frontend
```powershell
# Navigate to frontend directory
cd F:\Voice_Agent\frontend

# Start Vite development server
npm run dev
```
Open your browser to: `http://localhost:5173`

### Using the Application
1. Click **"Start a voice call"** on the Serenity Medical Clinic page.
2. Grant microphone access when prompted.
3. The frontend requests `/api/v1/livekit/token`, automatically dispatches Rachel ("clinical-voice-agent"), connects WebRTC audio, and Rachel greets you:
   > *"Hello! Thank you for calling Serenity Medical Clinic. I'm Rachel, your AI receptionist. How can I help you today?"*
4. Speak naturally to check doctor schedules, book an appointment, or ask questions about clinic hours and doctors.
5. Switch to the **Evaluation Dashboard** tab to run automated patient simulations and review ground-truth database results.

---

## Active Environment & Configuration Reference

```env
DATABASE_URL=sqlite:///./clinical_agent.db

LIVEKIT_URL=wss://live-interview-267n30oe.livekit.cloud
LIVEKIT_API_KEY=APIk3ZkJyHK4KtP
LIVEKIT_AGENT_NAME=clinical-voice-agent

LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-3.1-flash-lite

STT_PROVIDER=deepgram
TTS_PROVIDER=elevenlabs
ELEVENLABS_VOICE_ID=EXAVITQu4vr4xnSDxMaL
ELEVENLABS_MODEL_ID=eleven_turbo_v2_5

GOOGLE_CALENDAR_SANDBOX=true
CLINIC_TIMEZONE=America/New_York
```
