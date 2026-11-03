# Clinical Voice Agent — Project Context File
# Last updated: 2026-11-03T07:10:00+05:00
# Conversation: 094aad04-0ef0-4bba-8b4d-8b2fbe2fc6fa

## What Is This Project?

A **production-grade Clinical AI Receptionist** — a real-time voice agent that
answers patient calls, checks doctor availability against Google Calendar,
books / reschedules / cancels appointments, enforces clinical safety guardrails,
and can be autonomously evaluated against 35+ simulated patient scenarios.

**Free-Tier First**: Every external service uses a zero-cost plan (Groq Free,
Deepgram \$200 credit, ElevenLabs 10K chars, LiveKit Cloud 50 hrs/mo, Google
Calendar 1M req/day) with one-line config swap to paid tiers.

---

## Repository Location

```
F:\Voice_Agent\          (git: main branch)
Python:   3.12.14        (managed via uv, venv at .venv/)
Package Manager: uv 
```

---

## Completed Phase Summary (5 of 8 Phases Done)

| # | Phase | Commit | Tests |
|---|-------|--------|-------|
| 1 | Foundation & Data Architecture | `011c2f0` | 6 |
| 2 | Clinical Tools & Calendar Integration | `8878464` | 4 |
| 3 | Conversation State Machine & Guardrails | `1630dad` | 6 |
| 4 | LiveKit Cascaded Voice Agent Pipeline | `c8ebdd7` | 3 |
| 5 | Autonomous Evaluation & Simulated Patient | `8490421` | 4 |
| **Total** | | **5 commits** | **23 passing** |

### Remaining Phases

| # | Phase | Status |
|---|-------|--------|
| 6 | FastAPI REST API & LiveKit Token Service | ⏳ Next |
| 7 | React Voice Interface & Evaluation Dashboard | ⏳ Pending |
| 8 | E2E Validation, Docker & Production Runbook | ⏳ Pending |

---

## Full Project File Tree (41 files, 3398 Python LOC, ~150 KB)

```
F:\Voice_Agent\
├── .env.example                          # Environment config template (all providers)
├── .gitignore
├── pytest.ini                            # pythonpath=., asyncio auto mode
├── requirements.txt                      # 113 packages (livekit-agents, fastapi, sqlalchemy, etc.)
│
├── config/
│   ├── __init__.py
│   └── settings.py                       # Pydantic Settings — multi-provider LLM/STT/TTS/Calendar config
│
├── backend/
│   ├── __init__.py
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py                     # 8 SQLAlchemy ORM models (Patient, Doctor, Appointment,
│   │   │                                 #   Conversation, ConversationEvent, EvaluationRun,
│   │   │                                 #   EvaluationResult, AuditLog)
│   │   ├── connection.py                 # Engine factory (SQLite fallback / PostgreSQL), seed doctors
│   │   └── repositories.py              # Repository pattern: Patient, Doctor, Appointment, Audit repos
│   │
│   ├── api/
│   │   └── schemas/
│   │       ├── __init__.py
│   │       └── appointment_schemas.py    # Pydantic v2 request/response schemas for all API operations
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── calendar_service.py           # BaseCalendarService ABC + MockCalendarService (sandbox)
│   │   │                                 #   + GoogleCalendarService (live Google Calendar API v3)
│   │   └── appointment_service.py        # Core booking engine: slot calc, collision check, idempotency,
│   │                                     #   two-phase commit (Calendar→DB), reconciliation, rescheduling
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   └── clinical_tools.py             # 8 standalone tool functions callable by LLM or direct tests:
│   │                                     #   get_clinic_information, get_doctor_information,
│   │                                     #   check_availability, get_alternative_slots, book_appointment,
│   │                                     #   get_appointment, cancel_appointment, reschedule_appointment
│   │
│   └── agent/
│       ├── __init__.py
│       ├── prompts.py                    # RECEPTIONIST_SYSTEM_PROMPT, EXTRACTION_SYSTEM_PROMPT
│       ├── guardrails.py                 # Emergency detection (911), diagnosis refusal, privacy filter,
│       │                                 #   anti-hallucination booking verification
│       ├── state_manager.py              # ConversationState enum (12 states), BookingSlots model,
│       │                                 #   missing field tracker, next-question generator
│       ├── conversation_manager.py       # Full turn processor: guardrails → extraction → state machine
│       │                                 #   → tool calls → confirmation flow → hallucination filter
│       └── voice_agent.py                # LiveKit Agent worker: provider factories (build_llm/stt/tts/vad),
│                                         #   @function_tool registrations, create_clinical_agent(),
│                                         #   entrypoint(ctx), main() CLI runner
│
├── evaluation/
│   ├── __init__.py
│   ├── scenarios/
│   │   ├── __init__.py
│   │   └── scenario_definitions.py       # 15 EvaluationScenario definitions (TC-001 through TC-029)
│   │                                     #   across Categories A-F (Booking, Missing Info, Unavailable,
│   │                                     #   Conversation Mgmt, Safety)
│   ├── simulators/
│   │   ├── __init__.py
│   │   └── simulated_patient.py          # Autonomous patient persona: incremental disclosure,
│   │                                     #   confirmation handling, emergency termination
│   ├── evaluators/
│   │   ├── __init__.py
│   │   ├── task_evaluator.py             # Ground-truth DB state verifier (anti-hallucination gate)
│   │   ├── safety_evaluator.py           # 911 escalation / diagnosis refusal / privacy compliance
│   │   └── tool_evaluator.py             # Expected-vs-actual tool call accuracy scoring
│   └── runner.py                         # EvaluationRunner: closed-loop sim, per-turn latency tracking,
│                                         #   aggregate metrics, persistence to EvaluationRun/Result tables
│
└── tests/
    ├── __init__.py
    └── unit/
        ├── __init__.py
        ├── test_appointment_service.py   # 6 tests: slots, calendar events, booking, idempotency,
        │                                 #   double-booking prevention, cancellation
        ├── test_clinical_tools.py        # 4 tests: clinic info, doctor lookup, availability, lifecycle
        ├── test_conversation_manager.py  # 6 tests: emergency, diagnosis, privacy, anti-hallucination,
        │                                 #   state machine fields, full multi-turn booking
        ├── test_evaluation_engine.py     # 4 tests: single booking eval, emergency eval, diagnosis eval,
        │                                 #   batch suite persistence
        └── test_voice_agent_pipeline.py  # 3 tests: agent instantiation, tool callability, availability
```

---

## Key Architecture Decisions

### 1. Provider Abstraction (Pluggable Free ↔ Paid)
All LLM, STT, TTS, and Calendar providers are configured via environment variables
in `config/settings.py`. Switching from Groq free to OpenAI paid is a single
`.env` line change — no code modifications.

### 2. Deterministic Mock Calendar
`MockCalendarService` provides zero-cost, zero-network calendar operations with
pre-seeded busy slots and failure injection (`simulate_api_failure = True`).
Enabled by default via `GOOGLE_CALENDAR_SANDBOX=true`.

### 3. Two-Phase Booking with Reconciliation
`AppointmentService.book_appointment()` executes: Calendar Event Creation → DB
Record Insert. If DB fails after Calendar succeeds, it automatically rolls back
the calendar event to prevent orphaned bookings.

### 4. Anti-Hallucination Gate
`guardrails.verify_booking_hallucination()` intercepts agent output. If the agent
says "your appointment is confirmed" but no backend `book_appointment` tool call
actually succeeded, the message is rewritten to avoid false patient expectations.

### 5. LiveKit Agents v1.8+ API
The installed `livekit-agents==1.8.10` uses the new `Agent` + `AgentSession` API
(not the older `VoiceAssistant`). Tools are registered with `@function_tool`.

---

## Seeded Test Data

### Doctors (auto-seeded on DB init)
| ID | Name | Specialty | Hours |
|----|------|-----------|-------|
| DOC-001 | Dr. Ahmed Khan | General Physician | 09:00–17:00 |
| DOC-002 | Dr. Sarah Patel | Dermatologist | 10:00–16:00 |
| DOC-003 | Dr. Michael Chen | Cardiologist | 09:00–15:00 |

### Mock Calendar Pre-Booked Slots (DOC-001, 2026-11-03)
| Event ID | Time | Note |
|----------|------|------|
| mock-evt-1 | 09:30–10:00 | Review |
| mock-evt-2 | 11:00–11:30 | Follow-up |
| mock-evt-3 | 14:00–14:30 | Consultation |

---

## How to Run

```bash
# Activate environment
.venv\Scripts\activate

# Run all tests (23 tests, ~18s)
pytest -v

# Run voice agent worker (requires LiveKit credentials in .env)
python backend/agent/voice_agent.py dev

# Initialize database
python -c "from backend.database.connection import init_db; init_db()"
```

---

## External Dependencies & Versions
- Python 3.12.14 | uv package manager
- livekit-agents 1.8.10 | livekit 1.1.21
- livekit-plugins-openai 1.8.10 | livekit-plugins-deepgram 1.8.10
- livekit-plugins-elevenlabs 1.8.10 | livekit-plugins-silero 1.8.10
- fastapi 0.162.0 | uvicorn 0.54.0
- sqlalchemy 2.1.6 | alembic 1.20.1
- pydantic 2.14.2 | pydantic-settings 2.16.2
- google-api-python-client 2.201.0 | google-auth-oauthlib 1.5.0
- openai 3.42.1 | httpx 0.28.1
- pytest 9.2.0 | pytest-asyncio 1.4.1

---

## Ownership Handoff Status — 2026-11-03

This addendum supersedes the phase/branch snapshot above while retaining its original history. At initial audit the current branch was `dev/clinical-voice-agent-v1` at `229f7c5`; verified Phase 6 API foundation was committed as `463908e`. API integration coverage was added in `tests/integration/test_api_routes.py`. Full suite: 28 passed with one pytest cache permission warning. Phase 6 remains incomplete pending authentication/authorization and PHI access policy, plus a real LiveKit smoke test. See `PROJECT_MEMORY.md`, `DEVELOPMENT_ROADMAP.md`, and `phases.md` for the audit and remaining acceptance gates. No `prd.md` or `prd.docs/` directory was found in the repository.

Phase 7 now has a partial React + TypeScript + Vite frontend in `frontend/` (commit `041e68a`). `npm run build` passes with a large bundle warning; live browser/LiveKit verification is outstanding. The token route dispatches the configured named worker and grants a 30-minute token limited to microphone publish and subscription. Phase 8 Docker/Compose and runbook files are committed as `ba88c17`. Docker CLI is unavailable. `project_phases_Roadmap.md` remains pre-existing untracked user content.

