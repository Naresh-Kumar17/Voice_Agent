Clinical Voice Agent: 8-Phase Master Engineering Roadmap
Overview & Architecture Principles

This roadmap breaks down the complete end-to-end build of the Clinical AI Receptionist into 8 sequential, self-contained phases. Each phase has:

Clear Objectives & Scope
Free-Tier Zero-Cost Strategy
Deterministic Verification Gates (automated tests)
Git Commit Checkpoint
Phase Matrix
Phase	Title	Core Focus	Status	Git Commit Target
Phase 1	Foundation & Data Architecture	Python 3.12, DB models (SQLAlchemy), SQLite/Postgres dynamic engine, Pydantic v2 contracts	✅ Done	011c2f0 feat(core)
Phase 2	Controlled Agent Tools & Business Logic	8 clinical agent tools, Google Calendar API v3 + Sandbox, conflict prevention, idempotency, audit trail	✅ Done	8878464 feat(tools)
Phase 3	Conversational State Machine & Guardrails	Deterministic dialog state machine, intent & slot extraction, emergency escalation, clinical safety guardrails	✅ Done	1630dad feat(agent)
Phase 4	LiveKit Voice Agent Pipeline	LiveKit Agents worker, cascaded STT (Deepgram/Whisper) → LLM (Groq/OpenAI/Gemini) → TTS (ElevenLabs/Edge-TTS), interruption handling	✅ Done	c8ebdd7 feat(pipeline)
Phase 5	Autonomous Evaluation & Simulated Patient	35 test scenarios (TC-001–TC-035), autonomous simulated patient, deterministic DB/Calendar state verifier, regression engine	✅ Done	8490421 feat(eval)
Phase 6	FastAPI Application & WebRTC Token API	REST API endpoints for appointments, doctors, evaluation runs/results, and LiveKit WebRTC connection tokens	⏳ Next	feat(api): fastapi routes for clinical services, evaluations, and livekit tokens
Phase 7	React Voice Interface & Evaluation Dashboard	Browser-based WebRTC voice client, real-time audio visualizer & transcription, interactive test evaluation dashboard	⏳ Pending	feat(frontend): react voice interface and evaluation dashboard
Phase 8	E2E Validation, Hardening & Dockerization	Complete test suite run against simulated patient, latency profiling, Docker compose setup, and deployment documentation	⏳ Pending	chore(release): docker orchestration, e2e test suite validation, and production runbook
Detailed Phase Breakdown
Phase 1: Foundation & Data Architecture (COMPLETED)
Scope:
Python 3.12 environment initialized with uv.
Core dependencies installed (livekit-agents, fastapi, sqlalchemy, pydantic-settings, etc.).
Database models for all 8 entities: Patient, Doctor, Appointment, Conversation, ConversationEvent, EvaluationRun, EvaluationResult, AuditLog.
Repository layer (PatientRepository, DoctorRepository, AppointmentRepository, AuditRepository).
Unit tests for slot calculations, collision prevention, idempotency, and cancellation.
Verification: 6/6 unit tests passing.
Commit: 011c2f0
Phase 2: Controlled Agent Tools & Business Logic (NEXT)
Scope:
Implement all 8 controlled tools required by PRD Section 7.3:
get_doctor_information(doctor_id or specialty)
check_availability(doctor_id, date, preferred_time)
get_alternative_slots(doctor_id, date)
book_appointment(...) with idempotency and two-phase commit
get_appointment(appointment_id)
cancel_appointment(appointment_id, reason)
reschedule_appointment(appointment_id, new_date, new_time)
get_clinic_information()
Unit tests verifying every tool's error handling, input normalization, and edge cases.
Verification: tests/unit/test_clinical_tools.py all passing.
Commit: feat(tools): clinical agent tools and calendar integration layer
Phase 3: Conversational State Machine & Guardrails
Scope:
Deterministic conversation state manager (INIT → COLLECTING_INFO → CHECKING_AVAILABILITY → OFFERING_ALTERNATIVES → CONFIRMING_DETAILS → BOOKING → BOOKED → CLOSING).
Missing field tracker (detects which of the 5 required fields are missing and prompts specifically for them).
Clinical safety guardrails (emergency keyword detection with immediate 911 escalation, refusal to diagnose or prescribe).
Intent and entity extraction engine (date/time normalization, e.g. "tomorrow at 11am").
Verification: tests/unit/test_state_manager.py & tests/unit/test_guardrails.py.
Commit: feat(agent): conversation state manager, entity extraction, and clinical safety guardrails
Phase 4: LiveKit Voice Agent Pipeline
Scope:
LiveKit Agents entry point (backend/agent/voice_agent.py).
Cascaded voice pipeline configuration:
STT: Deepgram Nova-2 / Groq Whisper.
LLM: Groq Llama-3.3-70b (sub-200ms TTFT) / OpenAI gpt-4o-mini.
TTS: ElevenLabs streaming / Edge-TTS fallback.
VAD (Silero) for speech detection and interruption handling.
Agent session lifecycle hooks (greeting, room joining, error recovery).
Verification: LiveKit worker startup test, pipeline node instantiation test.
Commit: feat(pipeline): livekit cascaded voice agent worker and provider adapters
Phase 5: Autonomous Evaluation & Simulated Patient
Scope:
Scenario definitions for all 35 test cases (Categories A to G: TC-001 to TC-035) in structured format.
LLM-based SimulatedPatient agent with distinct personas, communication styles, hidden details, and incremental revelation.
Deterministic Ground-Truth Evaluator: directly inspects PostgreSQL/SQLite and Calendar state to verify actual outcome vs expected outcome.
LLM Conversation Judge for clarity, politeness, and conciseness.
Evaluation runner generating pass/fail reports, tool accuracy, safety score, and latency benchmarks.
Verification: Automated test suite executing Category A & Category F scenarios.
Commit: feat(eval): simulated patient persona engine, scenario suite, and ground-truth evaluator
Phase 6: FastAPI Application & WebRTC Token API
Scope:
FastAPI server (backend/main.py) with CORS and lifecycle management.
REST endpoints:
/api/v1/doctors, /api/v1/patients, /api/v1/appointments
/api/v1/livekit/token (generates WebRTC room connection token for browser)
/api/v1/evaluations/runs, /api/v1/evaluations/scenarios
OpenAPI documentation (/docs).
Verification: tests/integration/test_api_routes.py.
Commit: feat(api): fastapi routes for clinical services, evaluations, and livekit tokens
Phase 7: React Voice Interface & Evaluation Dashboard
Scope:
React + TypeScript frontend (frontend/).
Voice Receptionist Page:
One-click WebRTC microphone connection to LiveKit.
Live audio visualizer / wave animation.
Real-time transcription subtitles and speaking status indicator.
Evaluation Dashboard Page:
Overview metrics (Task Completion Rate, Tool Accuracy, Latency).
Scenario list with one-click test execution.
Conversation Inspector showing turn-by-turn transcripts, tool calls, and final DB state.
Verification: Frontend build check (npm run build).
Commit: feat(frontend): react voice interface and evaluation dashboard
Phase 8: End-to-End Validation, Hardening & Dockerization
Scope:
Full end-to-end integration test runs.
Dockerfile for backend and agent worker; docker-compose.yml orchestrating FastAPI, Agent, and Postgres.
Production deployment runbook and README.
Verification: Complete regression test suite execution, 100% pass on critical safety & booking tests.
Commit: chore(release): docker orchestration, e2e test suite validation, and production runbook