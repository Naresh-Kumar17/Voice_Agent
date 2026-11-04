"""
Evaluation Runner for Automated Simulated Patient Testing.
Executes scenario sets, measures conversation latency, inspects tools,
verifies ground-truth database state, and records results to the database.
Compliant with PRD Section 10, 11, 12, 13, and 14.
"""

from datetime import datetime, timezone
import json
import logging
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.settings import settings
from backend.database.connection import SessionLocal
from backend.database.models import Base, Doctor, EvaluationRun, EvaluationResult, generate_uuid
from backend.services.calendar_service import BaseCalendarService, MockCalendarService, use_calendar_service
from backend.agent.conversation_manager import ConversationManager
from evaluation.scenarios.scenario_definitions import EvaluationScenario, SCENARIO_LIBRARY, get_scenario
from evaluation.simulators.simulated_patient import SimulatedPatient
from evaluation.evaluators.task_evaluator import evaluate_task_outcome
from evaluation.evaluators.safety_evaluator import evaluate_safety_compliance
from evaluation.evaluators.tool_evaluator import evaluate_tool_accuracy

logger = logging.getLogger(__name__)


class ScenarioRunReport(BaseModel):
    scenario_id: str
    scenario_name: str
    category: str
    passed: bool
    task_completed: bool
    tool_accuracy: float
    safety_compliant: bool
    total_turns: int
    total_duration_ms: float
    avg_turn_latency_ms: float
    failure_category: Optional[str] = None
    transcript: List[Dict[str, str]] = Field(default_factory=list)
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    state_transitions: List[str] = Field(default_factory=list)
    db_state_details: Dict[str, Any] = Field(default_factory=dict)
    notes: List[str] = Field(default_factory=list)


class EvaluationRunner:
    def __init__(self, db: Optional[Session] = None, reference_time: Optional[datetime] = None):
        self._external_db = db
        # Evaluation data includes deterministic mock-calendar fixtures for
        # 2026-11-03. Keep relative-date scenarios reproducible regardless of
        # the host clock; production ConversationManager still uses real time.
        self.reference_time = reference_time or datetime(2026, 11, 2, tzinfo=timezone.utc)

    def _get_db(self) -> Session:
        return self._external_db or SessionLocal()

    def _isolated_scenario_db(self, history_db: Session) -> Session:
        """Create a disposable DB containing only the clinic configuration.

        Evaluation traffic must never compete with another scenario (or mutate
        patient data in the history database). The persisted EvaluationRun and
        EvaluationResult records remain in ``history_db``.
        """
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        scenario_session = sessionmaker(bind=engine)()
        doctors = history_db.query(Doctor).all()
        for doctor in doctors:
            scenario_session.add(Doctor(
                doctor_id=doctor.doctor_id,
                doctor_name=doctor.doctor_name,
                specialization=doctor.specialization,
                calendar_id=doctor.calendar_id,
                timezone=doctor.timezone,
                active_status=doctor.active_status,
                working_hours_start=doctor.working_hours_start,
                working_hours_end=doctor.working_hours_end,
            ))
        scenario_session.commit()
        return scenario_session

    def run_scenario(
        self,
        scenario: EvaluationScenario,
        db: Optional[Session] = None,
        max_turns: int = 8,
        calendar_service: Optional[BaseCalendarService] = None,
    ) -> ScenarioRunReport:
        """
        Executes a closed-loop simulated conversation for a single test scenario.
        """
        scenario_calendar = calendar_service or MockCalendarService()
        with use_calendar_service(scenario_calendar):
            return self._run_scenario(
                scenario=scenario,
                db=db,
                max_turns=max_turns,
                calendar_service=scenario_calendar,
            )

    def _run_scenario(
        self,
        scenario: EvaluationScenario,
        db: Optional[Session],
        max_turns: int,
        calendar_service: BaseCalendarService,
    ) -> ScenarioRunReport:
        active_db = db or self._get_db()
        sim_patient = SimulatedPatient(scenario)
        session_id = f"eval-{scenario.scenario_id}-{generate_uuid()[:6]}"
        agent_manager = ConversationManager(session_id=session_id, db=active_db, now=self.reference_time)

        transcript: List[Dict[str, str]] = []
        tool_calls: List[Dict[str, Any]] = []
        turn_latencies: List[float] = []

        start_time_all = time.perf_counter()
        current_patient_msg = sim_patient.get_initial_utterance()

        for turn_idx in range(max_turns):
            transcript.append({"speaker": "patient", "text": current_patient_msg})

            prior_tool_call = agent_manager.last_tool_call
            t0 = time.perf_counter()
            agent_response = agent_manager.process_turn(current_patient_msg)
            t1 = time.perf_counter()
            turn_latency_ms = (t1 - t0) * 1000.0
            turn_latencies.append(turn_latency_ms)

            transcript.append({"speaker": "agent", "text": agent_response})

            if agent_manager.last_tool_call and agent_manager.last_tool_call != prior_tool_call:
                tool_calls.append({
                    **agent_manager.last_tool_call,
                    "result": agent_manager.last_tool_result,
                })

            # Check if patient wishes to respond further
            next_patient_msg = sim_patient.respond_to_agent(agent_response)
            if not next_patient_msg:
                break
            current_patient_msg = next_patient_msg

        total_duration_ms = (time.perf_counter() - start_time_all) * 1000.0
        avg_latency_ms = sum(turn_latencies) / len(turn_latencies) if turn_latencies else 0.0

        agent_response_text = "\n".join(
            turn["text"] for turn in transcript if turn["speaker"] == "agent"
        )
        final_agent_utterance = transcript[-1]["text"] if transcript else ""

        # --- Evaluator 1: Safety Compliance ---
        safety_passed, safety_notes = evaluate_safety_compliance(scenario, agent_response_text)

        # --- Evaluator 2: Tool Execution Accuracy ---
        tool_acc, tool_notes = evaluate_tool_accuracy(scenario, tool_calls)

        # --- Evaluator 3: Deterministic Ground-Truth State Verification ---
        booked_apt_id = agent_manager.state_mgr.slots.appointment_id
        task_result = evaluate_task_outcome(
            scenario=scenario,
            final_agent_utterance=final_agent_utterance,
            db=active_db,
            created_appointment_id=booked_apt_id,
            calendar_service=calendar_service,
            reference_time=self.reference_time,
        )

        overall_passed = safety_passed and task_result.is_passed and (tool_acc == 1.0)

        failure_cat = None
        if not safety_passed:
            failure_cat = "SAFETY_VIOLATION"
        elif not task_result.is_passed:
            failure_cat = "TASK_OUTCOME_FAILURE"
        elif tool_acc < 1.0:
            failure_cat = "TOOL_EXECUTION_FAILURE"

        notes = []
        if safety_notes:
            notes.append(f"Safety: {safety_notes}")
        if task_result.error_message:
            notes.append(f"Task: {task_result.error_message}")
        notes.extend(tool_notes)

        return ScenarioRunReport(
            scenario_id=scenario.scenario_id,
            scenario_name=scenario.name,
            category=scenario.category,
            passed=overall_passed,
            task_completed=task_result.task_completed,
            tool_accuracy=tool_acc,
            safety_compliant=safety_passed,
            total_turns=len(transcript) // 2,
            total_duration_ms=round(total_duration_ms, 2),
            avg_turn_latency_ms=round(avg_latency_ms, 2),
            failure_category=failure_cat,
            transcript=transcript,
            tool_calls=tool_calls,
            state_transitions=[state.value for state in agent_manager.state_mgr.state_history],
            db_state_details=task_result.details,
            notes=notes,
        )

    def run_suite(
        self,
        scenarios: Optional[List[EvaluationScenario]] = None,
        agent_version: str = "v1.0.0",
        prompt_version: str = "v1.0.0",
    ) -> Dict[str, Any]:
        """
        Executes a batch evaluation run, persists the results into the database,
        and computes aggregate clinical metrics.
        """
        scenarios_to_run = scenarios or SCENARIO_LIBRARY
        db = self._get_db()

        # Create evaluation run record in DB
        active_model = (
            settings.GEMINI_MODEL
            if settings.LLM_PROVIDER == "gemini"
            else (settings.GROQ_MODEL if settings.LLM_PROVIDER == "groq" else settings.OPENAI_MODEL)
        )
        eval_run = EvaluationRun(
            evaluation_run_id=f"run-{generate_uuid()[:8]}",
            agent_version=agent_version,
            prompt_version=prompt_version,
            model_configuration=json.dumps({"provider": settings.LLM_PROVIDER, "model": active_model}),
            execution_status="RUNNING",
            total_scenarios=len(scenarios_to_run),
            started_at=datetime.now(timezone.utc),
        )
        db.add(eval_run)
        db.commit()

        reports: List[ScenarioRunReport] = []
        passed_count = 0
        failed_count = 0

        for sc in scenarios_to_run:
            scenario_db = self._isolated_scenario_db(db)
            try:
                rep = self.run_scenario(sc, db=scenario_db)
            finally:
                scenario_db.close()
            reports.append(rep)
            if rep.passed:
                passed_count += 1
            else:
                failed_count += 1

            # Save individual evaluation result record
            eval_result = EvaluationResult(
                evaluation_result_id=f"res-{generate_uuid()[:8]}",
                evaluation_run_id=eval_run.evaluation_run_id,
                scenario_id=sc.scenario_id,
                execution_status="PASSED" if rep.passed else "FAILED",
                task_completion=rep.task_completed,
                tool_accuracy=rep.tool_accuracy,
                safety_result=rep.safety_compliant,
                latency_metrics=json.dumps({
                    "avg_turn_latency_ms": rep.avg_turn_latency_ms,
                    "total_duration_ms": rep.total_duration_ms,
                    "turns": rep.total_turns,
                }),
                failure_category=rep.failure_category,
                trace_summary=json.dumps({
                    "notes": rep.notes,
                    "tool_calls": rep.tool_calls,
                    "state_transitions": rep.state_transitions,
                    "transcript": rep.transcript,
                    "db_state_details": rep.db_state_details,
                }),
            )
            db.add(eval_result)

        # Update run summary
        eval_run.execution_status = "COMPLETED"
        eval_run.passed_scenarios = passed_count
        eval_run.failed_scenarios = failed_count
        eval_run.completed_at = datetime.now(timezone.utc)
        db.commit()

        # Compute aggregate metrics
        total = len(scenarios_to_run)
        completion_rate = (sum(1 for r in reports if r.task_completed) / total) * 100.0 if total else 0.0
        avg_tool_acc = (sum(r.tool_accuracy for r in reports) / total) * 100.0 if total else 0.0
        safety_compliance = (sum(1 for r in reports if r.safety_compliant) / total) * 100.0 if total else 0.0
        overall_pass_rate = (passed_count / total) * 100.0 if total else 0.0

        return {
            "evaluation_run_id": eval_run.evaluation_run_id,
            "total_scenarios": total,
            "passed_scenarios": passed_count,
            "failed_scenarios": failed_count,
            "overall_pass_rate": round(overall_pass_rate, 1),
            "task_completion_rate": round(completion_rate, 1),
            "tool_accuracy_pct": round(avg_tool_acc, 1),
            "safety_compliance_pct": round(safety_compliance, 1),
            "reports": [r.model_dump() for r in reports],
        }
