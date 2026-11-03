# Clinical Voice Agent Web Client

React + TypeScript + Vite interface for the LiveKit voice receptionist and evaluation dashboard.

## Local development

1. Install the Python dependencies and configure the backend `.env` using the root `.env.example`.
2. Start the API: `uvicorn backend.main:app --reload --port 8000` from the repository root.
3. Start the frontend: `npm install` then `npm run dev` from `frontend/`.
4. Start the registered LiveKit worker with `python backend/agent/voice_agent.py dev` and configure `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, and matching `LIVEKIT_AGENT_NAME`.
5. Open the Vite URL (normally `http://localhost:5173`). Vite proxies `/api` and `/health` to the API during development.

For a separate production API host, set `VITE_API_BASE_URL` at build time. The browser requests a short lived participant token from the API and never receives the LiveKit API secret.

Build with `npm run build`; output is written to `dist/`.

## Current limits

- API routes are unauthenticated at this stage. Do not expose patient or evaluation endpoints publicly until an approved authentication, authorization, and patient-data access policy is implemented.
- Live calls require a reachable LiveKit server and a running worker registered under `LIVEKIT_AGENT_NAME`. Browser microphone access is required.
- The dashboard runs the current synchronous simulated evaluation suite; this does not test real audio or the external LLM/STT/TTS providers.
