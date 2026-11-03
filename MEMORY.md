# Clinical Voice Agent — Session Memory File
# Workspace: F:\Voice_Agent (git: main branch)
# Updated: 2026-11-03

---

## 1. Role & Engineering Philosophy

- Operating as **Lead AI Engineer** overseeing end-to-end voice agent architecture.
- Core Tenet: *"Conversational fluency is not task success."* Every appointment booking, cancellation, or rescheduling must be backed by a verified database record and calendar event.
- Free-Tier First: The entire stack operates reliably on free-tier service configurations (LiveKit Cloud 50 hrs/month, Deepgram $200 trial credit, ElevenLabs 10K free characters with premade voices, Google Gemini Free tier, and Google Calendar Sandbox).

---

## 2. Complete Phase Implementation Status (8 / 8 Phases Implemented)

### Phase 1: Foundation & Data Architecture ✅
- 8 SQLAlchemy models: `Patient`, `Doctor`, `Appointment`, `Conversation`, `ConversationEvent`, `EvaluationRun`, `EvaluationResult`, `AuditLog`.
- Repository pattern: `PatientRepo`, `DoctorRepo`, `AppointmentRepo`, `AuditRepo`.
- Pydantic v2 schemas for all request/response validation.
- `MockCalendarService` sandbox with deterministic busy slot fixtures and reset capability.
- `AppointmentService` with two-phase commit, collision prevention, idempotency, and cancellation.

### Phase 2: Controlled Agent Tools ✅
- 8 clinical tool functions: `get_clinic_information`, `get_doctor_information`, `check_availability`, `get_alternative_slots`, `book_appointment`, `get_appointment`, `cancel_appointment`, `reschedule_appointment`.
- Clean error compensation: old calendar events preserved if new event booking fails during rescheduling.

### Phase 3: Conversation State Machine & Guardrails ✅
- 12 conversation states: `INIT`, `IDENTIFY_INTENT`, `COLLECTING_INFO`, `CHECKING_AVAILABILITY`, `OFFERING_ALTERNATIVES`, `CONFIRMING_DETAILS`, `BOOKING`, `BOOKED`, `CANCELLED`, `RESCHEDULED`, `EMERGENCY_ESCALATED`, `CLOSING`.
- Safety guardrails: Emergency keyword detection → immediate 911 escalation; medical advice refusal; patient privacy protection.
- Anti-hallucination verification: `verify_booking_hallucination()` ensures the agent never states an appointment is confirmed without a real DB ID.

### Phase 4: LiveKit Voice Agent Pipeline ✅
- LiveKit Agents v1.8 `Agent` + `AgentSession` architecture.
- Multi-provider support with automatic fallback:
  - **LLM**: Gemini (`gemini-3.1-flash-lite` via Google OpenAI-compatible endpoint).
  - **STT**: Deepgram Nova-2 (`nova-2-general`).
  - **TTS**: ElevenLabs (`eleven_turbo_v2_5` with free-tier premade voice `EXAVITQu4vr4xnSDxMaL` / Bella).
  - **VAD**: Silero VAD for low-latency barge-in and turn detection.
- `@function_tool` registrations linking agent tools directly to clinical services.

### Phase 5: Autonomous Evaluation & Simulated Patient ✅
- 15 deterministic scenarios (TC-001 through TC-029) spanning booking, missing info, unavailability, cancellations, emergency escalation, and privacy.
- `SimulatedPatient` persona engine simulating incremental multi-turn patient dialogue.
- Independent evaluators: DB task verifier, safety auditor, tool accuracy calculator.
- Isolated in-memory SQLite instances and resettable calendar fixtures per test scenario.

### Phase 6: FastAPI REST API & LiveKit Token Service ✅
- `backend/main.py` FastAPI app with lifespan hooks and CORS middleware.
- `backend/api/routes/v1.py` endpoints:
  - `GET /health` — health check
  - `GET /api/v1/doctors` — list active doctors
  - `POST /api/v1/appointments/check` — check availability
  - `POST /api/v1/appointments` / `POST /api/v1/appointments/book` — book appointment
  - `DELETE /api/v1/appointments/{id}` — cancel appointment
  - `POST /api/v1/livekit/token` — creates a unique room, dispatches the named worker (`clinical-voice-agent`), and returns caller JWT token
  - `GET /api/v1/evaluations/scenarios`, `POST /api/v1/evaluations/run`, `GET /api/v1/evaluations/runs` — evaluation management

### Phase 7: React Frontend & Evaluation Dashboard ✅
- Modern React 19 + TypeScript + Vite single-page application under `frontend/`.
- Voice Receptionist Panel: LiveKit WebRTC client, microphone toggle, pulsating audio visualizer orb, real-time live subtitles/transcripts, call end controls.
- Evaluation Dashboard: scenario listing, single-click test execution, real-time metrics (task completion %, tool accuracy %, safety compliance %), and conversation inspection.
- Build verified with `npm run build` with zero TypeScript errors.

### Phase 8: Docker & Production Runbook ✅
- Multi-stage `Dockerfile` for Python backend/agent worker.
- `frontend/Dockerfile` and `frontend/nginx.conf` for optimized static asset serving.
- `docker-compose.yml` defining PostgreSQL, backend API, LiveKit worker, and frontend services.
- Detailed production deployment runbook in `README.md`.

---

## 3. Test Suite Verification

**Current status**: **43 / 43 automated tests pass** (`pytest -v` in ~36.9s):
- `tests/integration/test_api_routes.py`: 5 passed
- `tests/unit/test_appointment_service.py`: 9 passed
- `tests/unit/test_clinical_tools.py`: 4 passed
- `tests/unit/test_conversation_manager.py`: 9 passed
- `tests/unit/test_evaluation_engine.py`: 7 passed
- `tests/unit/test_voice_agent_pipeline.py`: 9 passed

---

## 4. Root Cause Analysis: Server Testing "status : not found"

When testing the server or inspecting the LiveKit Cloud dashboard, `"status : not found"` appeared due to the following reasons:

1. **LiveKit Cloud Worker Not Connected**:
   - In LiveKit Cloud, an agent status reports "not found" when no worker process is connected to the cloud project WebSocket and registered under `agent_name = "clinical-voice-agent"`.
   - **Resolution**: The worker must be launched using `python backend/agent/voice_agent.py dev` (or `start`). Once active, it registers with LiveKit Cloud and receives dispatches immediately.

2. **Gemini Model Name Incompatibility**:
   - `GEMINI_MODEL=gemini-3.8-flash` in the provided `.env` does not exist on Google's OpenAI-compatible endpoint (`https://generativelanguage.googleapis.com/v1beta/openai/`), returning HTTP 404/503 `status: NOT_FOUND` or `UNAVAILABLE`.
   - **Resolution**: Added automatic model fallback in `build_llm()` to normalize model names to `gemini-3.1-flash-lite`, which is active, fast, and stable.

3. **ElevenLabs Free Tier Voice Restrictions (HTTP 402)**:
   - Voice ID `21m00Tcm4TlvDq8ikWAM` ("Rachel") is a library voice that ElevenLabs restricts to paid subscribers (`paid_plan_required: Free users cannot use library voices via the API`).
   - **Resolution**: Added automatic fallback in `build_tts()` to `EXAVITQu4vr4xnSDxMaL` ("Bella"), a free premade voice supported across all free tiers.

4. **CLI Python Path Resolution**:
   - Running `python backend/agent/voice_agent.py` directly from PowerShell triggered `ModuleNotFoundError: No module named 'config'` because `sys.path` did not contain the repository root.
   - **Resolution**: Dynamically added workspace root to `sys.path` at the top of `backend/agent/voice_agent.py`.

---

## 5. Execution Runbook

### Service 1: FastAPI Backend
```powershell
cd F:\Voice_Agent
.venv\Scripts\activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
Swagger UI: `http://localhost:8000/docs`

### Service 2: LiveKit Voice Worker
```powershell
cd F:\Voice_Agent
.venv\Scripts\activate
python backend/agent/voice_agent.py dev
```

### Service 3: Frontend Web UI
```powershell
cd F:\Voice_Agent\frontend
npm run dev
```
Web App: `http://localhost:5173`
