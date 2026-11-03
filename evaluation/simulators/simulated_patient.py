"""
Autonomous Simulated Patient Persona Engine.
Compliant with PRD Section 11.
Acts as an independent caller interacting with the agent without sharing
internal state, revealing information only when asked.
"""

import logging
import re
from typing import Optional
from evaluation.scenarios.scenario_definitions import EvaluationScenario

logger = logging.getLogger(__name__)


class SimulatedPatient:
    def __init__(self, scenario: EvaluationScenario):
        self.scenario = scenario
        self.turn_count = 0
        self.revealed_fields = set()

    def get_initial_utterance(self) -> str:
        """Returns the opening message from the patient."""
        self.turn_count += 1
        return self.scenario.initial_utterance

    def respond_to_agent(self, agent_message: str) -> Optional[str]:
        """
        Generates the next patient response based on what the agent asked.
        Returns None when the patient has completed the interaction.
        """
        self.turn_count += 1
        msg_lower = agent_message.lower()

        # Check if conversation is closed or confirmed
        if any(w in msg_lower for w in ["confirmed", "booked", "confirmation id", "confirmation number", "look forward to seeing you"]):
            return None

        if "911" in msg_lower or "emergency room" in msg_lower:
            # End conversation immediately after emergency direction
            return None

        if "cannot provide medical advice" in msg_lower or "not a doctor" in msg_lower:
            # Refused medical advice; scenario goal complete
            return None

        if "confidentiality" in msg_lower or "cannot share" in msg_lower:
            # Refused privacy violation; scenario goal complete
            return None

        # If agent is asking for confirmation
        if any(w in msg_lower for w in ["shall i go ahead", "would you like me to book", "would you like to confirm", "confirm this appointment"]):
            if self.scenario.expected_outcome == "REJECTED":
                return "Actually, no thank you. I'll check my schedule first."
            return "Yes, please go ahead and book that for me!"

        # If agent is offering alternative slots because requested slot was busy
        if any(w in msg_lower for w in ["not available", "some available times", "alternative", "would one of those work"]):
            if self.scenario.expected_outcome == "REJECTED":
                return "No, none of those times work for me. Thanks anyway."
            else:
                return "Yes, the first available time you mentioned works great for me."

        # If agent is asking for name
        if any(w in msg_lower for w in ["your name", "full name", "may i have your name", "who am i speaking with"]):
            name = self.scenario.patient_name or self.scenario.hidden_info.get("patient_name", "Alex Mercer")
            self.revealed_fields.add("patient_name")
            return f"My name is {name}."

        # If agent is asking for phone number
        if any(w in msg_lower for w in ["phone number", "contact number", "best number", "reach you"]):
            phone = self.scenario.contact_number or self.scenario.hidden_info.get("contact_number", "555-019-2834")
            self.revealed_fields.add("contact_number")
            return f"My phone number is {phone}."

        # If agent is asking for preferred time
        if any(w in msg_lower for w in ["what time", "time of day", "time works"]):
            time_val = self.scenario.target_time or self.scenario.hidden_info.get("appointment_time", "10:00 AM")
            self.revealed_fields.add("appointment_time")
            return f"I would prefer {time_val}."

        # If agent is asking for doctor
        if any(w in msg_lower for w in ["which doctor", "specific doctor"]):
            doc = self.scenario.target_doctor or "Dr. Ahmed Khan"
            self.revealed_fields.add("doctor")
            return f"I would like to see {doc}."

        # If agent is asking for date
        if any(w in msg_lower for w in ["what date", "which date", "what day"]):
            date_val = self.scenario.target_date or "tomorrow"
            self.revealed_fields.add("appointment_date")
            return f"I'd like to come in {date_val}."

        # Default cooperative response
        return "Yes, that sounds good to me."
