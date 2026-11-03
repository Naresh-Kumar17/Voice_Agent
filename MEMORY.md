# Clinical Voice Agent — Session Memory File
# Purpose: Persistent engineering memory for resuming work across sessions.
# Last updated: 2026-11-03T07:10:00+05:00
# Workspace: F:\Voice_Agent (git main branch)
# Conversation: 094aad04-0ef0-4bba-8b4d-8b2fbe2fc6fa

---

## ROLE & DESIGN PHILOSOPHY

I am operating as **Lead AI Engineer** specializing in voice agent pipelines.

Core principle:
> "Conversational fluency is not task success."
> Every booking claim must be backed by a verified database record and calendar
> event. Anti-hallucination gates enforce this at every output boundary.

Design pillars:
1. **Free-tier zero-cost** — all providers have free tiers; paid swap is 1-line `.env` change.
2. **Deterministic backend** — state machine + idempotent DB ops + mock calendar sandbox.
3. **Closed-loop evaluation** — autonomous simulated patients + ground-truth DB assertions.

---

## COMPLETED WORK LOG

### Phase 1: Foundation & Data Architecture ✅
- **Commit**: `011c2f0` (19 files, 1546 LOC)
- Python 3.12 venv via `uv`, 113 packages installed.
- 8 SQLAlchemy models: Patient, Doctor, Appointment, Conversation, ConversationEvent, EvaluationRun, EvaluationResult, AuditLog.
- Repository pattern: PatientRepo, DoctorRepo, AppointmentRepo, AuditRepo.
- Pydantic v2 API schemas for all request/response contracts.
- Pydantic Settings for multi-provider env config.
- MockCalendarService (sandbox) + GoogleCalendarService (live).
- AppointmentService: slot calculation, collision detection, idempotency, two-phase commit with reconciliation.
- 6 unit tests passing.

### Phase 2: Controlled Agent Tools ✅
- **Commit**: `8878464` (4 files, 582 LOC)
- 8 clinical tool functions: get_clinic_information, get_doctor_information, check_availability, get_alternative_slots, book_appointment, get_appointment, cancel_appointment, reschedule_appointment.
- Added reschedule_appointment to AppointmentService (old calendar event deletion + new event creation + DB update).
- 4 unit tests: clinic info, doctor lookup, availability check, full booking lifecycle (book→get→reschedule→cancel→verify).

### Phase 3: Conversation State Machine & Guardrails ✅
- **Commit**: `1630dad` (6 files, 664 LOC)
- ConversationState enum: 12 states (INIT → IDENTIFY_INTENT → COLLECTING_INFO → CHECKING_AVAILABILITY → OFFERING_ALTERNATIVES → CONFIRMING_DETAILS → BOOKING → BOOKED → CANCELLED → RESCHEDULED → EMERGENCY_ESCALATED → CLOSING).
- BookingSlots model tracking 5 required fields (name, phone, doctor, date, time).
- Missing field tracker with natural-language next-question generator.
- Safety guardrails: emergency keyword regex (chest pain, stroke, seizure, etc.) → 911 directive; diagnosis/prescription refusal; privacy protection.
- Anti-hallucination filter: `verify_booking_hallucination()` catches false confirmation statements.
- Rule-based entity extractor: phone, date (tomorrow/today/ISO), time (10am/14:00), doctor name fuzzy match, appointment ID.
- ConversationManager: full multi-turn processor (guardrails → extraction → state transition → tool calls → confirmation flow).
- 6 unit tests: emergency escalation, diagnosis refusal, privacy refusal, anti-hallucination, state machine fields, full 4-turn booking.

### Phase 4: LiveKit Voice Agent Pipeline ✅
- **Commit**: `c8ebdd7` (25 files, 345 LOC)
- LiveKit Agents v1.8.10 uses `Agent` + `AgentSession` API (not deprecated `VoiceAssistant`).
- Provider factories: `build_llm()` (Groq via OpenAI-compat base_url / OpenAI direct), `build_stt()` (Deepgram / OpenAI fallback), `build_tts()` (ElevenLabs / OpenAI fallback), `build_vad()` (Silero).
- 6 `@function_tool` registrations wiring LLM tool-calling to clinical_tools functions.
- `create_clinical_agent()` factory composing instructions + tools + providers.
- `entrypoint(ctx)` lifecycle: connect → wait_for_participant → create agent → start session → greeting.
- `main()` for `python backend/agent/voice_agent.py dev` CLI.
- 3 unit tests: agent instantiation, tool callability, availability execution.
- **IMPORTANT**: Dummy API keys (`sk-dummy-test-key-for-local-dev`) used in STT/TTS/LLM fallbacks to prevent crash during local testing without real credentials.

### Phase 5: Autonomous Evaluation & Simulated Patient ✅
- **Commit**: `8490421` (12 files, 968 LOC)
- 15 EvaluationScenario definitions across Categories A-F (TC-001 to TC-029).
- SimulatedPatient persona engine: incremental disclosure, confirmation/rejection handling, immediate halt on 911/refusal/privacy.
- TaskOutcomeResult evaluator: directly inspects DB for Appointment record existence, status, patient name match, catches hallucinated confirmations.
- SafetyEvaluator: verifies 911 directive for emergencies, diagnosis refusal text, privacy refusal text.
- ToolEvaluator: expected-vs-actual tool call accuracy scoring.
- EvaluationRunner: orchestrates multi-turn sims, tracks per-turn latency, computes aggregate metrics (task completion, tool accuracy, safety compliance), persists EvaluationRun + EvaluationResult records to DB.
- **BUG FIXED**: SimulatedPatient was continuing conversation after safety refusals (emergency/diagnosis/privacy) — now returns `None` to terminate.
- **BUG FIXED**: Privacy keyword regex missed "neighbor" pattern in TC-029 — added `\bneighbor\b` and `\bif .+ has an appointment\b`.
- **BUG FIXED**: `runner.py` was missing `from config.settings import settings` — added import.
- 4 unit tests: booking scenario DB verification, emergency scenario 911 check, diagnosis refusal check, batch suite persistence.

---

## CURRENT AGGREGATE TEST STATUS

**23 / 23 tests passing** (~18 seconds)

| Test File | Tests | Status |
|-----------|-------|--------|
| test_appointment_service.py | 6 | ✅ All Pass |
| test_clinical_tools.py | 4 | ✅ All Pass |
| test_conversation_manager.py | 6 | ✅ All Pass |
| test_evaluation_engine.py | 4 | ✅ All Pass |
| test_voice_agent_pipeline.py | 3 | ✅ All Pass |

---

## WHAT REMAINS (Phases 6, 7, 8)

### Phase 6: FastAPI REST API & LiveKit Token Service
- `backend/main.py` — FastAPI app with CORS, lifespan hooks.
- `backend/api/routes/` — REST routes:
  - `GET /api/v1/doctors` — list active doctors
  - `POST /api/v1/appointments/check` — check availability
  - `POST /api/v1/appointments/book` — book appointment
  - `DELETE /api/v1/appointments/{id}` — cancel appointment
  - `POST /api/v1/livekit/token` — generate WebRTC connection token
  - `POST /api/v1/evaluations/run` — trigger eval suite
  - `GET /api/v1/evaluations/runs` — list eval runs
- `tests/integration/test_api_routes.py` — API integration tests.

### Phase 7: React Voice Interface & Evaluation Dashboard
- `frontend/` — React + TypeScript + Vite project
- Voice Receptionist Page: WebRTC mic connect, audio visualizer, live subtitles
- Evaluation Dashboard: metrics overview, scenario list, conversation inspector

### Phase 8: E2E Validation, Docker & Production Runbook
- Dockerfile + docker-compose.yml (FastAPI + Agent Worker + PostgreSQL)
- Full e2e regression suite execution
- README.md production deployment runbook

---

## KNOWN ISSUES / TECH DEBT

1. `git config core.autocrlf false` was set to suppress CRLF warnings — may need `.gitattributes` for cross-platform collaboration.
2. Rule-based entity extractor is deterministic but limited — will need LLM-based extraction for production edge cases (e.g. "next Tuesday at quarter past two").
3. Scenario library has 15 of 35 target scenarios — remaining 20 (Categories D-partial, E, G) need to be added.
4. No Alembic migration scripts yet — using `create_all()` for schema creation.
5. Patient name extraction regex `"my name is X Y"` doesn't handle complex names (hyphenated, multi-word surnames).

---

## ENVIRONMENT QUICK REFERENCE

```
Python:       3.12.14 (C:\Users\3tee\AppData\Roaming\uv\python\cpython-3.12)
Venv:         F:\Voice_Agent\.venv\
Activate:     .venv\Scripts\activate
Tests:        .venv\Scripts\pytest -v
Agent CLI:    .venv\Scripts\python backend/agent/voice_agent.py dev
DB Init:      .venv\Scripts\python -c "from backend.database.connection import init_db; init_db()"
Git user:     Naresh-Kumar17 <vishnaninaresh8@gmail.com>
```

---

## Ownership Handoff Update — 2026-11-03

Repository audit and current state are recorded in `PROJECT_MEMORY.md`; phase gates are in `DEVELOPMENT_ROADMAP.md` and `phases.md`. This update preserves the prior memory record above.

- Current branch is `dev/clinical-voice-agent-v1` at `229f7c5` (the older context below incorrectly called it `main`).
- Phase 6 API foundation was added: `backend/main.py`, versioned routes in `backend/api/routes/v1.py`, and five integration tests. Phase 6 remains partial because no authentication/authorization or PHI access policy exists and real LiveKit is unverified.
- Baseline 23 tests plus five API integration tests now pass: 28 passed; pytest emits one cache path permission warning.
- No PRD or `prd.docs/` folder was present. Existing untracked `project_phases_Roadmap.md` was preserved.
- No Git commit or push has yet been made for this work.

