"""HTTP API for clinic operations, evaluation, and LiveKit access tokens."""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from livekit import api as livekit_api
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config.settings import settings
from backend.database.connection import get_db
from backend.database.models import Appointment, Doctor, EvaluationResult, EvaluationRun, Patient
from backend.database.repositories import DoctorRepository, PatientRepository
from backend.services.appointment_service import AppointmentService
from backend.api.schemas.appointment_schemas import (
    AppointmentCreate, AppointmentResponse,
    AvailabilityRequest, AvailabilityResponse, DoctorResponse, PatientCreate,
    PatientResponse,
)
from evaluation.runner import EvaluationRunner
from evaluation.scenarios.scenario_definitions import SCENARIO_LIBRARY

router = APIRouter()


class LiveKitTokenResponse(BaseModel):
    server_url: str
    room_name: str
    participant_identity: str
    participant_token: str


class EvaluationRunRequest(BaseModel):
    scenario_ids: Optional[List[str]] = None


class RescheduleRequest(BaseModel):
    new_date: date
    new_time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")


class EvaluationRunSummary(BaseModel):
    evaluation_run_id: str
    execution_status: str
    total_scenarios: int
    passed_scenarios: int
    failed_scenarios: int
    started_at: Any
    completed_at: Any = None


def _doctor_response(doctor: Doctor) -> DoctorResponse:
    return DoctorResponse(
        doctor_id=doctor.doctor_id, doctor_name=doctor.doctor_name,
        specialization=doctor.specialization, calendar_id=doctor.calendar_id,
        timezone=doctor.timezone, active_status=doctor.active_status,
        working_hours_start=doctor.working_hours_start,
        working_hours_end=doctor.working_hours_end,
    )


def _appointment_service_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ValueError):
        return HTTPException(status_code=422, detail=str(exc))
    if isinstance(exc, ConnectionError):
        return HTTPException(status_code=503, detail="Scheduling service is unavailable")
    return HTTPException(status_code=500, detail="Appointment operation failed")


@router.get("/doctors", response_model=List[DoctorResponse])
def list_doctors(db: Session = Depends(get_db)):
    return [_doctor_response(d) for d in DoctorRepository(db).list_active()]


@router.get("/patients", response_model=List[PatientResponse])
def list_patients(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return (
        db.query(Patient)
        .order_by(Patient.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.post("/patients", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    existing = PatientRepository(db).get_by_phone(payload.phone_number.strip())
    if existing:
        raise HTTPException(status_code=409, detail="A patient with this phone number already exists")
    try:
        patient = PatientRepository(db).create(payload.full_name, payload.phone_number)
        return patient
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Patient could not be created")


@router.post("/appointments/check", response_model=AvailabilityResponse)
def check_appointment(payload: AvailabilityRequest, db: Session = Depends(get_db)):
    try:
        return AppointmentService(db).check_availability(
            payload.doctor_id, payload.appointment_date, payload.preferred_time
        )
    except Exception as exc:
        raise _appointment_service_error(exc)


@router.get("/appointments", response_model=List[AppointmentResponse])
def list_appointments(
    appointment_date: Optional[date] = None,
    doctor_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Appointment)
    if appointment_date:
        query = query.filter_by(appointment_date=appointment_date.isoformat())
    if doctor_id:
        query = query.filter_by(doctor_id=doctor_id)
    records = query.order_by(Appointment.appointment_date.asc(), Appointment.start_time.asc()).offset(offset).limit(limit).all()
    service = AppointmentService(db)
    return [service.get_appointment(a.appointment_id) for a in records]


@router.post("/appointments", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
@router.post(
    "/appointments/book",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def book_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)):
    try:
        return AppointmentService(db).book_appointment(payload)
    except Exception as exc:
        raise _appointment_service_error(exc)


@router.post("/appointments/{appointment_id}/reschedule", response_model=AppointmentResponse)
def reschedule_appointment(appointment_id: str, payload: RescheduleRequest, db: Session = Depends(get_db)):
    try:
        return AppointmentService(db).reschedule_appointment(
            appointment_id, payload.new_date.isoformat(), payload.new_time
        )
    except Exception as exc:
        raise _appointment_service_error(exc)


@router.get("/appointments/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(appointment_id: str, db: Session = Depends(get_db)):
    result = AppointmentService(db).get_appointment(appointment_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return result


@router.delete("/appointments/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_appointment(appointment_id: str, reason: str = Query("Patient requested cancellation", max_length=500), db: Session = Depends(get_db)):
    try:
        if not AppointmentService(db).cancel_appointment(appointment_id, reason):
            raise HTTPException(status_code=404, detail="Appointment not found or already cancelled")
    except HTTPException:
        raise
    except Exception as exc:
        raise _appointment_service_error(exc)


@router.post("/livekit/token", response_model=LiveKitTokenResponse)
async def create_livekit_token():
    if not (settings.LIVEKIT_URL and settings.LIVEKIT_API_KEY and settings.LIVEKIT_API_SECRET):
        raise HTTPException(status_code=503, detail="LiveKit is not configured")
    identity = f"caller-{uuid4().hex}"
    # Use a fresh server-generated room for every anonymous token to prevent
    # a caller from joining a room selected or shared by another caller.
    room_name = f"clinical-{uuid4().hex}"
    livekit_client = livekit_api.LiveKitAPI(
        settings.LIVEKIT_URL,
        settings.LIVEKIT_API_KEY,
        settings.LIVEKIT_API_SECRET,
    )
    try:
        await livekit_client.agent_dispatch.create_dispatch(
            livekit_api.CreateAgentDispatchRequest(
                agent_name=settings.LIVEKIT_AGENT_NAME,
                room=room_name,
            )
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Could not start the voice receptionist") from exc
    finally:
        await livekit_client.aclose()

    token = (
        livekit_api.AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
        .with_identity(identity)
        .with_name("Clinic caller")
        .with_ttl(timedelta(minutes=30))
        .with_grants(livekit_api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_publish_sources=["microphone"],
            can_publish_data=False,
            can_subscribe=True,
        ))
        .to_jwt()
    )
    return LiveKitTokenResponse(
        server_url=settings.LIVEKIT_URL, room_name=room_name,
        participant_identity=identity, participant_token=token,
    )


@router.get("/evaluations/scenarios")
def list_scenarios():
    return [scenario.model_dump() for scenario in SCENARIO_LIBRARY]


@router.post("/evaluations/run")
def run_evaluation(payload: EvaluationRunRequest, db: Session = Depends(get_db)):
    scenarios = SCENARIO_LIBRARY
    if payload.scenario_ids is not None:
        by_id = {scenario.scenario_id: scenario for scenario in SCENARIO_LIBRARY}
        unknown = sorted(set(payload.scenario_ids) - by_id.keys())
        if unknown:
            raise HTTPException(status_code=422, detail={"unknown_scenario_ids": unknown})
        scenarios = [by_id[scenario_id] for scenario_id in payload.scenario_ids]
    try:
        return EvaluationRunner(db=db).run_suite(scenarios=scenarios)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Evaluation run failed")


@router.get("/evaluations/runs", response_model=List[EvaluationRunSummary])
def list_evaluation_runs(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return db.query(EvaluationRun).order_by(EvaluationRun.started_at.desc()).offset(offset).limit(limit).all()


@router.get("/evaluations/runs/{run_id}")
def get_evaluation_run(run_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    run = db.query(EvaluationRun).filter_by(evaluation_run_id=run_id).first()
    if run is None:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    results = db.query(EvaluationResult).filter_by(evaluation_run_id=run_id).all()
    return {
        "evaluation_run_id": run.evaluation_run_id,
        "execution_status": run.execution_status,
        "total_scenarios": run.total_scenarios,
        "passed_scenarios": run.passed_scenarios,
        "failed_scenarios": run.failed_scenarios,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "results": [
            {"scenario_id": r.scenario_id, "execution_status": r.execution_status,
             "task_completion": r.task_completion, "tool_accuracy": r.tool_accuracy,
             "safety_result": r.safety_result, "latency_metrics": r.latency_metrics,
             "failure_category": r.failure_category, "trace_summary": r.trace_summary}
            for r in results
        ],
    }
