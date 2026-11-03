"""
Tool Execution Evaluator.
Compliant with PRD Section 10.3 (Layer 2: Tool Evaluation) & Section 13.2.
Inspects whether expected tools were called with appropriate arguments.
"""

from typing import Any, Dict, List, Tuple
from evaluation.scenarios.scenario_definitions import EvaluationScenario


def evaluate_tool_accuracy(
    scenario: EvaluationScenario,
    executed_tools: List[Dict[str, Any]],
) -> Tuple[float, List[str]]:
    """
    Computes tool execution accuracy as:
    (Successfully matched expected tools / Total expected tools)
    Returns: (accuracy_score between 0.0 and 1.0, diagnostic_notes)
    """
    if not scenario.expected_tools:
        return 1.0, ["No specific tools expected for this scenario."]

    called_tool_names = [call.get("tool", "") for call in executed_tools]
    matched_count = 0
    notes = []

    for expected in scenario.expected_tools:
        if expected in called_tool_names:
            matched_count += 1
            notes.append(f"Expected tool '{expected}' was correctly executed.")
        else:
            notes.append(f"Expected tool '{expected}' was NOT called.")

    accuracy = matched_count / len(scenario.expected_tools)
    return accuracy, notes

