# Clinical Voice Agent

An administrative voice receptionist that answers clinic questions and supports appointment availability, booking, cancellation, and rescheduling. The existing deterministic appointment service and safety guardrails back both the LiveKit worker and the FastAPI API. Simulated evaluation scenarios inspect conversation outcomes and database state.

## Current implementation status

- Phases 1–5: substantial implementation exists, but the phase audit marks gaps and verification work; this is not a claim of full completion.
- Phase 6: FastAPI service and LiveKit token/agent dispatch API exist. Authentication and authorization for patient and evaluation data are not implemented.
- Phase 7: React voice client and evaluation dashboard exist. Live browser calls still require a configured LiveKit project and running agent worker.
- Phase 8: container files and this deployment guide are present. Docker could not be run in the development environment, and production release gates remain open.

The original handoff PRD (`prd.md`) and `prd.docs/` were absent. See [PROJECT_MEMORY.md](PROJECT_MEMORY.md), [phases.md](phases.md), and [DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md) for the source/code audit, phase matrix, risks, and remaining acceptance criteria. The pre-existing `project_phases_Roadmap.md` remains intact.

## Local development

Python 3.12 is used by the current workspace. Activate the existing virtual environment or create one, install `requirements.txt`, copy `.env.example` to `.env`, and configure required providers.

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```

The API health endpoint is `GET /health`; interactive API documentation is at `/docs`. Start the worker in a second shell with `python -m backend.agent.voice_agent dev` from the repository root. For the frontend, run `npm ci` and `npm run dev` from `frontend/`; the development server proxies API requests to port 8000.

Run validation with:

```powershell
python -m pytest -q
cd frontend
npm ci
npm run build
```

## Container deployment (development/staging only)

1. Install Docker Engine/Desktop with the Compose plugin.
2. Copy `.env.example` to `.env`. Set a long random `POSTGRES_PASSWORD`, a unique `SECRET_KEY`, LiveKit URL/key/secret, and the selected LLM/STT/TTS credentials. Keep `GOOGLE_CALENDAR_SANDBOX=true` until real calendar credentials and behavior are verified.
3. Ensure `POSTGRES_PASSWORD` uses URL-safe alphanumeric characters for the current SQLAlchemy URL interpolation.
4. Start the stack: `docker compose up --build -d`.
5. Check health with `docker compose ps`, `curl http://127.0.0.1:8000/health`, and open `http://127.0.0.1:8080` for the frontend. API and frontend ports bind to host ports in the compose file; place them behind TLS and an access-controlled reverse proxy before any shared environment.
6. Inspect logs with `docker compose logs -f api agent frontend postgres`.
7. Stop without deleting data with `docker compose down`. **Do not use `docker compose down -v`** unless the PostgreSQL data is intentionally being destroyed.

The persistent `postgres_data` volume stores the database. Current startup uses SQLAlchemy `create_all()` and seeds baseline doctors; Alembic revisions and tested backup/restore procedures are not yet present. Back up the volume before upgrades.

## Release blockers

Do not expose this stack to patients or the public yet. Patient and appointment endpoints, evaluation routes, and token issuance have no application authentication, authorization, rate limiting, or audit policy. Define and implement those controls before deployment. The current API returns patient phone numbers and appointment records to unauthenticated callers. Set up TLS, secrets management, backups, monitoring, and a privacy/security review as part of that work.

The LiveKit worker, Google Calendar adapter, provider credentials, Docker image build, Compose health checks, and browser audio flow were not validated against real external services in this environment. The evaluation runner tests the deterministic `ConversationManager`, not actual speech recognition, model responses, or synthesized audio.
