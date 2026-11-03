# Clinical Voice Agent Development Roadmap

Audit date: 2026-11-03. This roadmap preserves the established eight-phase structure from the existing `project_phases_Roadmap.md`. That pre-existing untracked file remains untouched. The original PRD and `phases.md` named in the handoff were not present, so this roadmap is based on the available context, memory, roadmap, code, and tests.

## Initial stopping point (before this ownership pass)

Development is at the start of Phase 6. Five feature commits exist through evaluation, then the current branch `dev/clinical-voice-agent-v1` has commit `229f7c5`. Baseline is 23 passing unit tests. The current implementation has 15 evaluation scenarios and no HTTP API, frontend, E2E, Docker, or production runbook. No real provider credentials/infrastructure have been verified.

## Ordered work and acceptance gates

| Order | Phase / work | Priority and dependencies | Measurable acceptance criteria |
|---|---|---|---|
| 1 | Phase 6: FastAPI application and LiveKit token API | Next; depends on current SQLAlchemy services and token policy | `backend.main:app` starts; OpenAPI lists versioned routes for doctors, patients, appointments, evaluations, scenarios and token; validation/errors map to HTTP statuses; DB lifecycle is configurable for tests; token route never returns secrets and fails clearly when not configured; integration tests cover success/error paths; existing 23 tests remain green. |
| 2 | Phase 7: React + TypeScript voice client and evaluation dashboard | Foundation implemented; needs browser/LiveKit verification | `frontend/` builds; voice UI requests token and connects, plays remote audio and subscribes to transcriptions; dashboard loads runs/scenarios, starts whole or individual scenarios, and inspects simulated transcript/tool summary; loading/empty/error states are present. Remaining: live worker/browser test, measured audio visualizer, browser interaction coverage, bundle splitting. |
| 3 | Phase 8: E2E, hardening, Docker and runbook | Next; API access policy is a required production gate; external credentials needed for live voice | Docker Compose starts API, worker and PostgreSQL with health checks; schema setup is repeatable; E2E covers booking and safety refusal; critical regression suite passes; production runbook documents secrets, setup, health checks and limitations; no secrets committed. |
| 4 | Phase 1 gap closure: migration history and supported DB dependencies | Before production deployment; preserve current SQLite data | Alembic migration upgrades a clean DB and current schema; PostgreSQL dependency is declared; tests validate schema creation and upgrade without dropping user data. |
| 5 | Phase 2 reliability: calendar errors, cancellation/reschedule compensation and input edges | Before production; can proceed alongside phases | Calendar outage never reports false availability; create/delete failures preserve or flag reconciliation state; date/time/phone validation returns controlled errors; tests cover partial failures and audit outcomes. |
| 6 | Phase 3 conversation completion | Before production voice workflow acceptance | Reschedule intent is end-to-end; state transitions reject invalid moves; safety regression tests include varied phrasing and false-positive checks; limitations are explicit. |
| 7 | Phase 4 provider verification | Requires provider credentials and LiveKit room | Mock lifecycle test covers connection, participant, session and failures; credentialed smoke test establishes real audio path; remove dummy-key success appearance and report missing config clearly. |
| 8 | Phase 5 evaluation completeness | Before claiming the 35-scenario requirement | TC-001–TC-035 are defined or source requirements are revised; evaluator checks outcome, arguments, calendar and safety; runner records failures reliably; critical suites pass through the intended voice/runtime path where feasible. |

## Risks and sequencing constraints

- Phase 7 depends on a stable Phase 6 token and evaluation response schema.
- Phase 8 production deployment depends on resolving DB migrations, provider configuration, and calendar failure semantics.
- The source PRD is absent; do not invent new product behavior beyond the available phase roadmap/context. In particular, API authorization and PHI listing policy require an explicit project decision before exposing patient data broadly.
- Live Google Calendar and LiveKit verification cannot be claimed without configured credentials and external services.
- Keep `clinical_agent.db` and the pre-existing untracked `project_phases_Roadmap.md` intact.

## Milestone record

### Initial ownership assessment

- Completed: source/doc/history inventory, baseline test run, architecture and phase audit.
- Files changed: `PROJECT_MEMORY.md`, `DEVELOPMENT_ROADMAP.md`, `phases.md`.
- Tests: `.venv\Scripts\python.exe -m pytest -q` -> 23 passed, one cache permission warning.
- Commit: assessment documents and Phase 6 work were included in `463908e`.
- Remaining: continue with Phase 6 requirements (especially approved authorization policy), then proceed in order while maintaining these documents.

### Phase 6 API foundation

- Completed: FastAPI application/lifespan, health and OpenAPI, doctors/patients/appointments routes, rescheduling, LiveKit token creation, evaluation scenario/run/list/detail endpoints, request date/time validation.
- Files changed: `backend/main.py`, `backend/api/routes/__init__.py`, `backend/api/routes/v1.py`, `backend/api/schemas/appointment_schemas.py`, `tests/integration/test_api_routes.py`.
- Tests: `.venv\Scripts\python.exe -m pytest tests\integration\test_api_routes.py -q` -> 5 passed; full `.venv\Scripts\python.exe -m pytest -q` -> 28 passed. Both show a pytest cache permission warning. Live services were not contacted.
- Commit: `463908e` (API foundation; this includes the Phase 6 base routes, prior to named-worker dispatch hardening).
- Remaining: agree and implement authentication/authorization and PHI access boundaries; evaluate background execution for evaluation runs; test against configured LiveKit and deployment database. Phase 6 is partially complete, not production-ready.

### Phase 7 frontend foundation

- Completed: responsive React voice interface and evaluation dashboard, token-based LiveKit client, agent dispatch, transcription/audio hooks, individual scenario runs, saved run inspector.
- Files changed: `frontend/` app and package lock, `backend/api/routes/v1.py`, `backend/agent/voice_agent.py`, `config/settings.py`, `evaluation/runner.py`, `tests/integration/test_api_routes.py`, `.env.example`.
- Tests: `npm run build` -> passed (one Vite chunk-size warning: 815.26 KB minified JS); `.venv\Scripts\python.exe -m pytest -q` -> 28 passed, one pytest cache permission warning.
- Commit: pending.
- Remaining: no browser interaction or live LiveKit test (service credentials/worker unavailable); orb is a connection/speaking indicator, not a waveform; simulated transcript persisted in trace; bundle needs code splitting. Phase 7 is partial.
