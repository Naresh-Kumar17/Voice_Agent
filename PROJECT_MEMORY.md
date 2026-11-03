# Clinical Voice Agent Project Memory

Audit date: 2026-11-03 (Asia/Karachi)  
Repository: `F:\Voice_Agent`  
Branch at audit: `dev/clinical-voice-agent-v1`  
Audited commit: `229f7c5` (parent `1b38666`)

## Project purpose and scope

A clinical receptionist voice agent for administrative calls: answer clinic and doctor questions, check appointment availability, book/cancel/reschedule visits, and route emergency or medical advice requests to safe responses. The target callers are clinic patients; clinic staff configure providers and operate the evaluation/deployment systems. Primary use cases are voice appointment lifecycle operations, clinic information, and safety escalation/refusal.

Intended provider adapters include LiveKit, LLM, STT, TTS, Google Calendar and a deterministic mock calendar. SQLite is the local default, with PostgreSQL intended for deployment. The project favors deterministic booking state and ground-truth evaluation. The repository does not yet implement a browser UI, REST API, deployment stack, authentication, or a migration history.

## Documentation and source-of-truth audit

The request referenced `context.md`, `memory.md`, `prd.md`, `phases.md`, and `prd.docs/`. The repository instead contains uppercase `CONTEXT.md`, uppercase `MEMORY.md`, and untracked `project_phases_Roadmap.md`. No `prd.md`, `phases.md`, or `prd.docs/` exists. The cited PRD sections in source comments are therefore unavailable for direct verification. `CONTEXT.md`, `MEMORY.md`, and the existing roadmap are the available intent records; source and tests establish what currently runs. The pre-existing untracked roadmap was not modified.

The context/memory files say five phases are complete, 23 tests pass, and Phases 6–8 remain. The current baseline supports the test claim (23 passed). However, several phase descriptions overstate implementation: there are 15 evaluation scenarios, not 35; voice-agent tests instantiate components and tools but do not connect to LiveKit or exercise audio; and there is no API, frontend, E2E suite, Docker, or production runbook. The current branch differs from the `main` branch stated in context. The latest branch commit `229f7c5` appears to add one-line files to the evaluation/test areas and project context; implementation work is in the earlier feature commits.

## Architecture and data flow

```text
Caller audio -> LiveKit AgentSession -> provider STT/LLM/TTS -> registered clinical tools
                                                        -> AppointmentService
                                                           -> SQLAlchemy repositories / DB
                                                           -> Calendar service (mock or Google)
Evaluation scenarios -> SimulatedPatient -> ConversationManager -> tools/services
                       -> safety/tool/task evaluators -> EvaluationRun/Result DB rows
```

- **Configuration:** `config/settings.py` loads Pydantic Settings from `.env` and environment variables. `.env.example` documents provider values. Settings currently include a development secret default and provider defaults; production validation is absent.
- **Database:** `backend/database/models.py` defines Patient, Doctor, Appointment, Conversation, ConversationEvent, EvaluationRun, EvaluationResult, and AuditLog. `connection.py` builds a global engine/session factory, `create_all()` schema setup and seeds three doctors. SQLite is used locally. No migrations are present.
- **Persistence:** `backend/database/repositories.py` provides patient, doctor, appointment and audit repositories. Conversation/evaluation persistence also occurs directly through SQLAlchemy in the runner.
- **Scheduling:** `backend/services/appointment_service.py` calculates 30-minute slots and buffers, checks calendar and DB state, performs booking and audit logging, and provides cancel/reschedule. `calendar_service.py` implements mock and Google Calendar adapters. Booking is calendar-first then DB with attempted compensation; rescheduling deletes the old event before creating a new one, leaving a failure window.
- **API contracts:** `backend/api/schemas/appointment_schemas.py` has Pydantic request/response models, but no HTTP API/routes currently exist.
- **Agent:** `backend/agent/state_manager.py` tracks twelve conversation states and five required booking slots; `guardrails.py` handles emergency, advice, privacy and false-confirmation text; `conversation_manager.py` runs deterministic extraction/state/tool logic; `prompts.py` contains LiveKit agent instructions; `voice_agent.py` configures provider factories, six LiveKit tools and worker lifecycle.
- **Tools:** `backend/tools/clinical_tools.py` exposes eight synchronous functions that construct their own session when one is not injected, then delegate to services.
- **Evaluation:** `evaluation/scenarios/scenario_definitions.py` contains 15 of the planned 35 scenarios. `simulated_patient.py` is rule-driven, not an independent LLM. `runner.py` evaluates `ConversationManager`, not LiveKit audio/LLM behavior; evaluators inspect tool names, transcript safety and DB appointment state.
- **Tests:** `tests/unit/` has 23 unit tests across scheduling, tools, conversation safety/state, evaluation, and LiveKit construction. No integration/API/frontend/E2E tests currently exist.

## Directory and major-file map

| Path | Responsibility |
|---|---|
| `backend/database/` | ORM models, engine/session setup, seeds, repositories |
| `backend/api/schemas/` | Pydantic API/tool contracts (HTTP routes absent at baseline) |
| `backend/services/` | Appointment orchestration and calendar providers |
| `backend/tools/` | Clinical functions called by the agent or tests |
| `backend/agent/` | State machine, guardrails, deterministic conversation manager, LiveKit worker and prompt |
| `config/settings.py` | Environment-backed configuration |
| `evaluation/scenarios/` | Scenario definitions and lookup helpers |
| `evaluation/simulators/` | Rule-based simulated caller |
| `evaluation/evaluators/` | Task, safety, and tool scoring |
| `evaluation/runner.py` | Scenario orchestration, aggregation, evaluation persistence |
| `Dockerfile`, `docker-compose.yml` | Python API/worker images and Postgres/API/agent/frontend orchestration |
| `README.md` | Local setup, container runbook and current release blockers |
| `frontend/` | React/TypeScript/Vite voice client and evaluation dashboard; API client and LiveKit browser connection |
| `tests/unit/` | Baseline unit tests |
| `.env.example` | Configuration template; never copy secrets into tracked files |
| `requirements.txt` | Python dependency ranges |
| `pytest.ini` | Pytest import/async settings |
| `clinical_agent.db` | Existing local SQLite database; preserve user data |

## Phase completion matrix

Status definitions follow the requested scale. COMPLETED means implemented and adequately validated; component existence alone is insufficient.

| Phase | Status | Objectives and requirements | Implemented and evidence | Gaps, issues, dependencies and remaining acceptance criteria |
|---|---|---|---|---|
| 1. Foundation & Data Architecture | PARTIALLY COMPLETED | Python stack, eight entities, repositories, SQLite/Postgres, contracts, deterministic scheduling and persistence | ORM, settings, schemas, repositories, connection and appointment/calendar services exist; PostgreSQL driver is declared; unit tests cover slot generation, booking, idempotency, conflict and cancellation | No Alembic revision history or migration consistency check; no DB integration coverage. Accept when supported DBs initialize from migrations without data loss and relevant repository/service tests pass. |
| 2. Controlled Tools & Business Logic | PARTIALLY COMPLETED | Eight tools, calendar adapter, validation, failure handling, booking/cancel/reschedule and audit | Eight functions and mock/Google adapters exist; tests cover basic lifecycle | Validation/error-edge coverage incomplete; Google adapter has not been exercised against credentials; missing Google configuration can make availability appear empty; cancellation swallows calendar deletion errors; reschedule ordering can lose old calendar event on failure. Accept with adapter tests and safe compensation/error semantics. |
| 3. Conversation State & Guardrails | PARTIALLY COMPLETED | Slot collection, intent/entity extraction, dialogue flow, emergency/advice/privacy and false booking protection | State manager, regex extractor, conversation manager, guardrails, six tests | State transitions are not validated; reschedule intent is extracted but not handled; extraction has known date/time/name limitations; guardrail coverage is regex-limited. Accept with lifecycle intent and safety tests plus transition validation. |
| 4. LiveKit Voice Pipeline | NEEDS VERIFICATION | Provider adapters, worker/session lifecycle, interruption and actual voice operation | Worker, six function tools, provider factory, three instantiation/tool tests; Gemini OpenAI-compatible LLM adapter is now wired and locally configured | No credentialed room/audio/worker or Gemini request test; default API key fallbacks are dummy values; Edge TTS remains unimplemented; no explicit error recovery/interruption tests. Accept with mocked lifecycle coverage and credentialed deployment smoke test documented. |
| 5. Autonomous Evaluation | PARTIALLY COMPLETED | 35 scenarios, autonomous caller, deterministic DB/calendar verifier, metrics, latency, persistence, conversation judging | 15 scenarios; rule-based simulator; DB/safety/tool evaluators; runner and four tests | 20 planned cases absent, no LLM conversation judge, tool arguments not scored, calendar state not independently verified, run errors do not reliably mark runs FAILED. Accept when all TC-001–TC-035 are represented and critical safety/booking cases pass against intended agent path. |
| 6. FastAPI & LiveKit Token API | PARTIALLY COMPLETED | Doctor/patient/appointment, evaluation, scenario and LiveKit token endpoints; lifecycle, CORS and OpenAPI | `backend/main.py`, `backend/api/routes/v1.py`, five passing API integration tests | No authorization policy; PHI listings and evaluation operations currently unauthenticated; no real LiveKit verification. Accept with approved access control, route integration tests, and documented live token smoke test. |
| 7. React Voice Interface & Dashboard | PARTIALLY COMPLETED | WebRTC microphone UI, subtitles/audio state, metrics, scenario runner and inspector | `frontend/src/` voice panel, dashboard and API client; `frontend/README.md` | No browser interaction tests or live LiveKit verification; orb is not an audio waveform; detail transcript is simulated; production JS is 815 KB. Accept with browser and configured worker tests, and sensible code splitting. |
| 8. E2E, Hardening & Docker | PARTIALLY COMPLETED | E2E regression, latency/security checks, Docker Compose with API/worker/Postgres and runbook | `Dockerfile`, `docker-compose.yml`, `frontend/Dockerfile`, `frontend/nginx.conf`, `.dockerignore`, `README.md`; API integration covers service workflows | Docker engine unavailable; no full browser/live-service E2E; no migration/backup validation; authentication and PHI access unresolved. Accept after container startup/health tests, browser/provider checks, security policy, and documented data recovery. |

## Git and validation record

- Recent feature history: `011c2f0` foundation; `8878464` tools; `1630dad` conversation/guardrails; `c8ebdd7` LiveKit pipeline; `8490421` evaluation; `1b38666` context and memory; `229f7c5` architecture/implementation branch commit; `463908e` API foundation; `041e68a` frontend/dashboard and worker-dispatch hardening.
- Remote `origin` is configured as `https://github.com/mk-2007/Voice_Agent.git`; no push was requested separately beyond the pasted request's conditional instruction.
- Initial working tree: only `project_phases_Roadmap.md` untracked. Preserve it and do not include it in project commits.
- Baseline validation: `.venv\Scripts\python.exe -m pytest -q` -> **23 passed** in 8.64s, one pytest cache permission warning. No API/integration test existed at baseline.
- Environment: Python 3.12 venv is present. Existing `clinical_agent.db` is user/project data and must not be deleted or reset.

## Phase 6 implementation update (2026-11-03)

Phase 6 is now **partially implemented**. Added `backend/main.py` with FastAPI lifespan DB initialization, health check, CORS and OpenAPI metadata; `backend/api/routes/v1.py` provides doctor/patient routes, appointment check/book/list/get/cancel/reschedule, server-generated LiveKit room tokens and named-worker dispatch, and evaluation scenarios/run/list/detail endpoints. Appointment request schemas now reject malformed calendar dates and times. The `/appointments/book` path is retained as a compatibility alias while `/appointments` is the documented create route. The token is limited to microphone publishing/subscription, a unique room, and 30 minutes.

`tests/integration/test_api_routes.py` adds five API-level tests using isolated shared in-memory SQLite. They cover OpenAPI/health/doctors; appointment lifecycle and invalid inputs; duplicate patient behavior; evaluation run persistence and lookup; and LiveKit missing-configuration, dispatch failure, unique-room and token generation behavior. Full validation: **28 passed** (23 pre-existing unit + 5 integration), with the pre-existing pytest cache permission warning. No real LiveKit or calendar credentials were used. Phase 6 still needs an explicit authentication/authorization and patient-data access design before production; API listing and synchronous evaluation operations are currently unauthenticated.

Files changed for this milestone: `backend/main.py`, `backend/api/routes/__init__.py`, `backend/api/routes/v1.py`, `backend/api/schemas/appointment_schemas.py`, `backend/agent/voice_agent.py`, `config/settings.py`, and `tests/integration/test_api_routes.py`. Documentation updates are in `phases.md` and `DEVELOPMENT_ROADMAP.md`. API foundation commit: `463908e`. No push was performed.

## Phase 7 implementation update (2026-11-03)

Added a React + TypeScript + Vite frontend under `frontend/`: voice connection, microphone control, LiveKit remote audio playback and transcription events, connection/errors/loading states, responsive clinic layout, evaluation metrics, run selection and details, per-scenario run controls, and simulated transcript/tool-call inspection. The token endpoint now explicitly dispatches the registered agent before the browser connects; the worker agent name is configurable. UI README has local run instructions and limitations.

Validation: `npm run build` passes using installed dependencies. Vite reports one performance warning: JS bundle 815.26 KB minified (225.82 KB gzip). Python full suite remains **28 passed**. Browser access to actual LiveKit/media and transcription was not available; no browser interaction test exists. Phase 7 remains partial, pending real service checks and workflow validation. Verified frontend milestone commit: `041e68a`.

## Phase 8 deployment foundation (2026-11-03)

Added API/agent `Dockerfile`, Compose with Postgres/API/agent/frontend, health checks for database/API/frontend, persistent Postgres volume, frontend multi-stage image and Nginx API proxy, `.dockerignore`, and root deployment README. Declared `psycopg2-binary` for the existing PostgreSQL URL format. Compose ports bind to localhost by default. YAML parsed successfully with PyYAML. Docker/Compose is not installed, so no image or startup test was run. Authentication, migrations, backup/restore, live external services, and browser E2E remain blockers; Phase 8 is partial.

- Local commits on `dev/clinical-voice-agent-v1`: `463908e` (`feat(api): add clinical service and evaluation routes`) and `041e68a` (`feat(frontend): add voice client and evaluation dashboard`).
- Docker/README/Phase 8 additions are in `ba88c17`. No push performed.
- Latest Python validation: 28 passed, one pytest cache permission warning. Latest frontend validation: Vite production build passes with the noted large-chunk warning.

## Gemini local configuration update (2026-11-03)

The user supplied a Gemini API key. It is stored only in ignored local `.env` with `LLM_PROVIDER=gemini`; no key value is copied into tracked files or logs. Added `build_llm()` support for Google's OpenAI-compatible endpoint, `x-goog-api-client` identification, and the current stable `gemini-3.8-flash` model default. Config loading confirms the provider/model/key are present without printing the credential. Two provider-configuration tests were added; full suite: **30 passed** with the existing pytest cache warning. No request was sent to Gemini. LiveKit, STT and TTS credentials are still absent; live calls remain unavailable.

## Known risks and implementation order

1. Complete Phase 6 by defining authentication/authorization and patient-data access policy, then test the policy on patient, appointment and evaluation routes. Consider moving longer evaluation jobs out of synchronous HTTP requests.
2. Make API token policy explicit: signed LiveKit token requires configured credentials, server URL, unique identity and room grant; never expose API secret.
3. Phase 7 frontend consumes the stable API contract and only the server-issued token.
4. Phase 8 deployment, E2E, migration and security hardening.
5. In parallel with completion gates: fix/test scheduling compensation and cancellation, safe calendar unavailability, rescheduling intent and evaluation accuracy.

No phase has been declared fully complete solely because its files exist. External provider validation requires credentials and infrastructure not present in this workspace.
