"""
Clinical Safety Guardrails for the Voice Agent.
Compliant with PRD Section 2.2 and Section 17.3:
- Real-time emergency escalation detection.
- Refusal of clinical diagnosis, drug prescriptions, and dosages.
- Patient privacy protection.
- Ground-truth confirmation verification (anti-hallucination filter).
"""

import re
from typing import Optional, Tuple

EMERGENCY_KEYWORDS = [
    r"\bchest pain\b",
    r"\bheart attack\b",
    r"\bcan't breathe\b",
    r"\bcannot breathe\b",
    r"\bdifficulty breathing\b",
    r"\bshortness of breath\b",
    r"\bsevere bleeding\b",
    r"\bheavily bleeding\b",
    r"\bunconscious\b",
    r"\blost consciousness\b",
    r"\bstroke\b",
    r"\bface drooping\b",
    r"\bseizure\b",
    r"\boverdose\b",
    r"\bsuicid",
    r"\bpoison",
]

DIAGNOSIS_KEYWORDS = [
    r"\bdiagnos",
    r"\bwhat do i have\b",
    r"\bwhat disease\b",
    r"\bwhat illness\b",
    r"\bwhat condition\b",
    r"\bwhat medicine\b",
    r"\bwhat medication\b",
    r"\bwhat antibiotic\b",
    r"\bwhat drug\b",
    r"\bwhat dose\b",
    r"\bwhat dosage\b",
    r"\bprescribe\b",
    r"\bcure my\b",
]

PRIVACY_KEYWORDS = [
    r"\bother patient\b",
    r"\bsomeone else\b",
    r"\banyone else\b",
    r"\bsomeone else's appointment\b",
    r"\banother patient\b",
    r"\bneighbor\b",
    r"\bwho is visiting\b",
    r"\bpatient list\b",
    r"\bmedical history of\b",
    r"\bif .+ has an appointment\b",
]

EMERGENCY_RESPONSE = (
    "If you are experiencing a medical emergency, please hang up immediately "
    "and call 911 or proceed to the nearest emergency room. "
    "I am an administrative AI receptionist and cannot provide emergency medical care."
)

CLINICAL_ADVICE_REFUSAL = (
    "I am an administrative receptionist and cannot provide medical advice, "
    "diagnose conditions, or recommend medications. Our physicians would be happy "
    "to evaluate your health during an in-person consultation."
)

PRIVACY_REFUSAL = (
    "To protect patient confidentiality and comply with healthcare privacy regulations, "
    "I cannot share information regarding other patients."
)


def check_emergency(text: str) -> Tuple[bool, Optional[str]]:
    """Checks whether the text describes an acute medical emergency."""
    text_lower = text.lower()
    for pattern in EMERGENCY_KEYWORDS:
        if re.search(pattern, text_lower):
            return True, EMERGENCY_RESPONSE
    return False, None


def check_medical_advice(text: str) -> Tuple[bool, Optional[str]]:
    """Checks whether the text is soliciting medical diagnosis or prescription."""
    text_lower = text.lower()
    for pattern in DIAGNOSIS_KEYWORDS:
        if re.search(pattern, text_lower):
            return True, CLINICAL_ADVICE_REFUSAL
    return False, None


def check_privacy_violation(text: str) -> Tuple[bool, Optional[str]]:
    """Checks whether the user is attempting to access another patient's data."""
    text_lower = text.lower()
    for pattern in PRIVACY_KEYWORDS:
        if re.search(pattern, text_lower):
            return True, PRIVACY_REFUSAL
    return False, None


def evaluate_input_guardrails(user_utterance: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Evaluates all input guardrails.
    Returns: (is_blocked, response_message, violation_category)
    """
    # 1. Emergency Escalation (highest priority)
    is_emergency, em_resp = check_emergency(user_utterance)
    if is_emergency:
        return True, em_resp, "EMERGENCY_ESCALATION"

    # 2. Medical advice / diagnosis
    is_med_advice, med_resp = check_medical_advice(user_utterance)
    if is_med_advice:
        return True, med_resp, "MEDICAL_ADVICE_REFUSAL"

    # 3. Privacy violation
    is_privacy, priv_resp = check_privacy_violation(user_utterance)
    if is_privacy:
        return True, priv_resp, "PRIVACY_VIOLATION"

    return False, None, None


def verify_booking_hallucination(agent_utterance: str, has_confirmed_booking: bool) -> str:
    """
    Verifies that the agent response does not assert an appointment is confirmed
    if no actual booking was completed in the backend.
    """
    confirmation_triggers = [
        "your appointment is confirmed",
        "i have booked your appointment",
        "appointment has been scheduled",
        "you're all booked",
    ]
    agent_lower = agent_utterance.lower()
    for trigger in confirmation_triggers:
        if trigger in agent_lower and not has_confirmed_booking:
            # Override hallucinated statement
            return (
                "I have collected your preferences, but I haven't finalized the booking yet. "
                "Would you like me to go ahead and confirm this appointment for you?"
            )
    return agent_utterance

