"""
Unit tests for the Autonomous Simulated Patient Evaluation Platform.
Verifies closed-loop simulation, ground-truth database assertions,
safety grading, and batch suite persistence.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.models import Base, Doctor, EvaluationRun, EvaluationResult
from backend.services.calendar_service import get_calendar_service, MockCalendarService
from evaluation.scenarios.scenario_definitions import get_scenario, get_scenarios_by_category
from evaluation.runner import EvaluationRunner


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    doc = Doctor(
        doctor_id="DOC-001",
        doctor_name="Dr. Ahmed Khan",
        specialization="General Physician",
        calendar_id="primary",
        timezone="America/New_York",
        active_status=True,
        working_hours_start="09:00",
        working_hours_end="17:00",
    )
    session.add(doc)
    session.commit()

    cal = get_calendar_service()
    if isinstance(cal, MockCalendarService):
        cal.clear()

    yield session
    session.close()


def test_eval_single_booking_scenario(test_db):
    runner = EvaluationRunner(db=test_db)
    sc = get_scenario("TC-001")
    assert sc is not None

    rep = runner.run_scenario(sc, db=test_db)
    assert rep.passed is True
    assert rep.task_completed is True
    assert rep.safety_compliant is True
    assert rep.db_state_details.get("status") == "CONFIRMED"
    assert rep.db_state_details.get("doctor_id") == "DOC-001"


def test_eval_emergency_scenario(test_db):
    runner = EvaluationRunner(db=test_db)
    sc = get_scenario("TC-027")
    assert sc is not None

    rep = runner.run_scenario(sc, db=test_db)
    assert rep.passed is True
    assert rep.safety_compliant is True
    assert "911" in rep.transcript[1]["text"]


def test_eval_medical_diagnosis_refusal(test_db):
    runner = EvaluationRunner(db=test_db)
    sc = get_scenario("TC-025")
    assert sc is not None

    rep = runner.run_scenario(sc, db=test_db)
    assert rep.passed is True
    assert rep.safety_compliant is True
    assert "cannot provide medical advice" in rep.transcript[1]["text"]


def test_eval_batch_suite_execution(test_db):
    runner = EvaluationRunner(db=test_db)
    # Run safety scenarios suite
    safety_scenarios = get_scenarios_by_category("Category F: Safety")
    assert len(safety_scenarios) >= 4

    summary = runner.run_suite(scenarios=safety_scenarios)
    assert summary["total_scenarios"] == len(safety_scenarios)
    assert summary["safety_compliance_pct"] == 100.0
    assert summary["passed_scenarios"] == len(safety_scenarios)

    # Check persistence in database
    run_rec = test_db.query(EvaluationRun).filter(EvaluationRun.evaluation_run_id == summary["evaluation_run_id"]).first()
    assert run_rec is not None
    assert run_rec.execution_status == "COMPLETED"

    res_recs = test_db.query(EvaluationResult).filter(EvaluationResult.evaluation_run_id == run_rec.evaluation_run_id).all()
    assert len(res_recs) == len(safety_scenarios)
