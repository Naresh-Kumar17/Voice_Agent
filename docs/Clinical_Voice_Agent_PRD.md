# Clinical Voice Agent

## Product Requirements Document (PRD)

**Version:** 1.0\
**Date:** November 2, 2026\
**Product:** AI-Powered Clinical Receptionist\
**Architecture:** LiveKit Agents + Custom Python Agent\
**Status:** Initial Development Specification

------------------------------------------------------------------------

# 1. Executive Summary

## 1.1 Product Overview

The Clinical Voice Agent is an AI-powered conversational receptionist
designed to automate administrative interactions between patients and
healthcare clinics.

The system communicates with patients through a browser-based voice
interface, understands their requests, collects necessary information,
interacts with the clinic's appointment management infrastructure, and
provides accurate verbal responses.

The initial implementation uses LiveKit Agents as the real-time voice
communication infrastructure and a custom Python-based agent for
conversational intelligence, workflow management, and business logic.

The application integrates with Google Calendar for appointment
availability and scheduling, PostgreSQL for persistent data storage, and
ElevenLabs for natural voice generation.

A dedicated evaluation and testing platform is developed alongside the
agent. This platform simulates patient conversations, executes
predefined scenarios, inspects tool execution, verifies database and
calendar outcomes, measures performance, and identifies behavioral
regressions.

The product initially operates through a browser-based voice interface.
Phone integration through Twilio and WhatsApp Business API integration
are explicitly deferred.

## 1.2 Product Vision

Build a reliable, conversational AI receptionist that can independently
handle routine clinic administration while maintaining predictable
behavior, accurate appointment management, and measurable performance.

**A successful conversation does not necessarily represent a successful
task.**

The agent must be evaluated on what it actually accomplishes, not merely
on how naturally it communicates.

## 1.3 Primary Objectives

1.  Develop a natural, real-time voice interaction system.
2.  Implement a clinic-specific conversational agent using Python.
3.  Automate appointment information collection and scheduling.
4.  Integrate Google Calendar for real-time availability checking.
5.  Maintain persistent patient, appointment, and conversation records.
6.  Develop an automated simulated-patient testing system.
7.  Establish deterministic evaluation of actual agent outcomes.
8.  Measure conversational quality, accuracy, reliability, and latency.
9.  Establish an extensible architecture for future communication
    channels.

------------------------------------------------------------------------

# 2. Product Scope

## 2.1 Initial Product Scope

  Component                            Included
  ------------------------------------ ----------
  Browser-based voice interface        Yes
  LiveKit real-time communication      Yes
  Custom Python AI agent               Yes
  Speech-to-text                       Yes
  LLM-based reasoning                  Yes
  ElevenLabs text-to-speech            Yes
  Conversation state management        Yes
  Appointment information extraction   Yes
  Google Calendar integration          Yes
  Appointment booking                  Yes
  Appointment availability checking    Yes
  Alternative slot suggestions         Yes
  PostgreSQL database                  Yes
  Conversation persistence             Yes
  Automated simulated patients         Yes
  Automated evaluation engine          Yes
  Evaluation dashboard                 Yes
  Real-time performance monitoring     Yes
  Twilio phone integration             Deferred
  WhatsApp Business API                Deferred
  Medical diagnosis                    No
  Prescription generation              No
  Autonomous clinical decisions        No

## 2.2 Out of Scope

The initial product is an administrative receptionist, not a medical
practitioner.

It must not:

-   Diagnose medical conditions.
-   Recommend medications.
-   Prescribe treatments.
-   Make independent clinical decisions.
-   Claim that a doctor is available without checking the scheduling
    system.
-   Invent appointment confirmations.
-   Provide emergency medical assessment.

When a caller describes an emergency, the agent must follow a
predefined, clinic-approved escalation procedure.

------------------------------------------------------------------------

# 3. Target Users

## 3.1 Patients

Patients interact with the voice agent to:

-   Request appointments.
-   Identify available doctors.
-   Ask about clinic timings.
-   Provide personal information.
-   Change appointment preferences.
-   Cancel existing appointments.
-   Obtain booking confirmation.

## 3.2 Clinic Administrators

Clinic administrators manage:

-   Doctor information.
-   Doctor availability.
-   Working hours.
-   Appointment schedules.
-   Patient records.
-   Operational settings.
-   Agent performance.

## 3.3 Developers and Evaluators

Developers use the evaluation platform to:

-   Create test scenarios.
-   Execute simulations.
-   Inspect conversations.
-   Analyze failed interactions.
-   Compare model versions.
-   Evaluate prompt modifications.
-   Verify backend operations.
-   Monitor system performance.

------------------------------------------------------------------------

# 4. System Architecture

## 4.1 Architectural Overview

The application follows a modular architecture consisting of five major
subsystems:

1.  Voice Interaction Infrastructure.
2.  AI Agent and Conversation Management.
3.  Backend and Business Services.
4.  Data and External Integrations.
5.  Evaluation and Testing Infrastructure.

The evaluation infrastructure operates independently of normal
patient-facing conversations while sharing the same agent implementation
and business logic.

## 4.2 High-Level Architecture

``` text
PATIENT
   |
REACT FRONTEND
   |
WEBRTC / LIVEKIT
   |
LIVEKIT AGENT SESSION
   |
CUSTOM PYTHON VOICE AGENT
   |
CONVERSATION MANAGER
   |
INTENT IDENTIFICATION
   |
INFORMATION EXTRACTION
   |
STATE MACHINE
   |
CONTROLLED AGENT TOOLS
   |
FASTAPI BUSINESS SERVICES
   |
POSTGRESQL DATABASE
   |
GOOGLE CALENDAR API
   |
VERIFIED OPERATION RESULT
   |
AGENT RESPONSE
   |
ELEVENLABS TEXT-TO-SPEECH
   |
PATIENT

Parallel subsystem:

EVALUATION PLATFORM
   |
SCENARIO MANAGER
   |
SIMULATED PATIENT
   |
LIVE AGENT EXECUTION
   |
CONVERSATION INSPECTION
   |
TOOL EXECUTION INSPECTION
   |
DATABASE AND CALENDAR VERIFICATION
   |
EVALUATION ENGINE
   |
METRICS AND REPORTING
   |
EVALUATION DASHBOARD
```

## 4.3 Technology Stack

  -----------------------------------------------------------------------
  Layer                   Technology              Purpose
  ----------------------- ----------------------- -----------------------
  Frontend                React                   Voice interaction
                                                  interface

  Frontend language       JavaScript / TypeScript Frontend implementation

  Audio communication     WebRTC                  Real-time audio

  Real-time               LiveKit                 Audio sessions and
  infrastructure                                  transport

  Voice framework         LiveKit Agents          Voice agent runtime

  Agent implementation    Python                  Conversational and
                                                  workflow logic

  Backend framework       FastAPI                 Application APIs

  LLM                     OpenAI model selected   Reasoning and
                          through benchmarking    conversation

  Speech-to-text          Provider integrated     Speech transcription
                          through LiveKit         

  Text-to-speech          ElevenLabs              Natural voice
                                                  generation

  Database                PostgreSQL              Persistent application
                                                  data

  ORM                     SQLAlchemy              Database operations

  Database migrations     Alembic                 Schema versioning

  Data validation         Pydantic                Typed input and output
                                                  validation

  Calendar                Google Calendar API     Appointment scheduling

  Testing                 Pytest                  Automated tests

  Simulation              LiveKit Agent           Simulated conversations
                          Simulations             

  Custom evaluation       Python                  Grading and reporting

  Deployment              Docker                  Reproducible deployment

  Version control         Git and GitHub          Source control
  -----------------------------------------------------------------------

Exact model versions and voice configurations must be selected through
evaluation rather than permanently hardcoded.

------------------------------------------------------------------------

# 5. Voice Interaction Infrastructure

## 5.1 LiveKit Integration

LiveKit Agents provides the real-time communication infrastructure. The
application does not implement low-level WebRTC audio streaming
independently.

Responsibilities include:

-   Managing real-time audio sessions.
-   Establishing communication between frontend and agent.
-   Receiving microphone input.
-   Publishing generated audio.
-   Managing speaking and listening states.
-   Handling interruptions.
-   Managing conversational turns.
-   Supporting real-time transcription.

## 5.2 Initial Interaction Workflow

1.  Patient opens the clinic website.
2.  Patient clicks **Start Conversation**.
3.  Frontend requests microphone permission.
4.  Frontend establishes a LiveKit connection.
5.  Agent joins the communication session.
6.  Agent introduces itself.
7.  Patient begins speaking.
8.  Audio is processed through the voice pipeline.
9.  Agent generates a response.
10. Response is delivered as audio.

## 5.3 Voice Pipeline

The initial architecture uses a cascaded pipeline:

``` text
SPEECH INPUT
     |
SPEECH-TO-TEXT
     |
LANGUAGE MODEL
     |
AGENT BUSINESS LOGIC
     |
TEXT-TO-SPEECH
     |
SPEECH OUTPUT
```

The cascaded architecture is preferred initially because each stage can
be independently inspected, tested, and replaced.

## 5.4 Voice Requirements

The system must support:

-   Natural conversation.
-   Real-time transcription.
-   Interruption handling.
-   Appropriate pauses.
-   Clear speech output.
-   Recovery from temporary connection failures.
-   Detection of incomplete user input.
-   Appropriate handling of silence.
-   Configurable language and voice settings.

The initial supported languages must be selected and validated before
release. English should be included in the first test suite. Urdu and
other clinic-relevant languages should be introduced only after
dedicated speech-recognition and voice-quality evaluation.

------------------------------------------------------------------------

# 6. AI Agent Architecture

## 6.1 Agent Design

The agent is implemented in Python using the LiveKit Agents framework.

The agent owns conversational reasoning and tool selection, while
deterministic Python services own application state and business
operations.

The initial implementation uses a single conversational agent rather
than multiple autonomous agents. This reduces complexity and makes the
system easier to evaluate.

## 6.2 Agent Components

### A. Conversation Manager

Responsibilities:

-   Maintain conversational context.
-   Track collected information.
-   Manage incomplete requests.
-   Maintain session information.
-   Control conversation progression.

### B. Intent Identification

The system must identify the patient's purpose.

Supported initial intents:

-   `BOOK_APPOINTMENT`
-   `CHECK_AVAILABILITY`
-   `RESCHEDULE_APPOINTMENT`
-   `CANCEL_APPOINTMENT`
-   `CLINIC_INFORMATION`
-   `DOCTOR_INFORMATION`
-   `GENERAL_ADMINISTRATIVE_QUERY`
-   `HUMAN_ASSISTANCE`
-   `EMERGENCY_ESCALATION`
-   `UNKNOWN`

### C. Information Extraction

The agent converts conversational input into structured information.

Example patient input:

> I want to see Dr. Ahmed tomorrow around eleven.

Expected extraction:

``` json
{
  "intent": "BOOK_APPOINTMENT",
  "doctor_name": "Dr. Ahmed",
  "appointment_date": "2026-11-03",
  "preferred_time": "11:00",
  "patient_name": null,
  "contact_number": null
}
```

The extraction process must support:

-   Missing information.
-   Ambiguous dates.
-   Relative dates.
-   Different time expressions.
-   Corrections.
-   Information provided in different orders.
-   Repeated information.

### D. Information Collection

The agent identifies which required fields remain incomplete and asks
only the necessary follow-up questions.

It should not repeatedly request information already provided.

### E. State Management

A deterministic state machine controls the booking workflow.

The LLM must not independently decide that a booking is complete. The
backend validates every state transition.

------------------------------------------------------------------------

# 7. Appointment Booking Workflow

## 7.1 Booking Information

  Field              Requirement
  ------------------ -------------
  Patient name       Required
  Contact number     Required
  Doctor             Required
  Appointment date   Required
  Appointment time   Required
  Appointment type   Conditional
  Additional notes   Optional

Only information necessary for administrative scheduling should be
collected. The clinic defines which appointment types and additional
fields are required.

## 7.2 Booking State Machine

``` text
START
  |
  v
IDENTIFY INTENT
  |
  v
COLLECT INFORMATION
  |
  v
VALIDATE INFORMATION
  |
  v
CHECK CALENDAR AVAILABILITY
  |
  v
IS SLOT AVAILABLE?
  |
  +---- NO ----> OFFER ALTERNATIVES
  |                    |
  |                    v
  |             PATIENT SELECTS
  |                    |
  |                    v
  |             RECHECK AVAILABILITY
  |                    |
  +--------------------+
  |
  v
CONFIRM DETAILS WITH PATIENT
  |
  v
VERIFY FINAL AVAILABILITY
  |
  v
CREATE APPOINTMENT
  |
  v
VERIFY CALENDAR EVENT
  |
  v
SAVE DATABASE RECORD
  |
  v
SPEAK CONFIRMATION
  |
  v
END
```

## 7.3 Required Agent Tools

The agent has access to controlled Python functions.

### Tool 1: `get_doctor_information()`

Returns doctor information and scheduling configuration.

### Tool 2: `check_availability()`

Parameters:

-   `doctor_id`
-   `appointment_date`
-   `preferred_time`

Returns:

-   Availability status.
-   Requested time.
-   Available alternatives.
-   Doctor working hours.

### Tool 3: `get_alternative_slots()`

Returns alternative appointments when the requested slot is unavailable.

### Tool 4: `book_appointment()`

Parameters:

-   `patient_id`
-   `doctor_id`
-   `appointment_date`
-   `appointment_time`
-   `appointment_type`
-   `idempotency_key`

Must validate availability and patient confirmation before booking.

### Tool 5: `get_appointment()`

Retrieves an existing appointment.

### Tool 6: `cancel_appointment()`

Cancels an existing appointment after identity verification and
confirmation.

### Tool 7: `reschedule_appointment()`

Changes an existing appointment after checking availability.

### Tool 8: `get_clinic_information()`

Returns approved clinic information.

## 7.4 Booking Integrity

The system must never rely exclusively on the LLM's understanding of
appointment availability.

All scheduling decisions must be validated by backend services.

The booking operation must:

1.  Validate patient information.
2.  Validate doctor information.
3.  Check the requested slot.
4.  Prevent conflicting bookings.
5.  Verify explicit patient confirmation.
6.  Create the calendar event.
7.  Persist the database record.
8.  Verify successful completion.
9.  Return the actual booking result.

The system must implement idempotency to prevent duplicate appointments
when requests are retried.

If the calendar operation succeeds but database persistence fails, the
backend must reconcile the operation rather than silently creating
another event.

------------------------------------------------------------------------

# 8. Google Calendar Integration

## 8.1 Purpose

Google Calendar acts as the external scheduling system for the initial
release.

Each doctor should have a corresponding calendar or an explicitly
configured scheduling calendar.

## 8.2 Required Operations

-   Authenticate with Google.
-   Access authorized calendars.
-   Retrieve free/busy information.
-   Determine available slots.
-   Create events.
-   Retrieve existing events.
-   Update events.
-   Delete or cancel events.

## 8.3 Availability Workflow

1.  Receive doctor ID.
2.  Retrieve calendar configuration.
3.  Determine clinic timezone.
4.  Calculate requested appointment interval.
5.  Query Google Calendar free/busy information.
6.  Compare results against clinic working hours.
7.  Apply appointment duration and buffer rules.
8.  Return available slots.

## 8.4 Calendar Security

Use OAuth 2.0 and the narrowest appropriate permissions.

Where possible, separate availability access from event-creation
permissions.

The application must never expose Google access tokens to the frontend
or LLM.

## 8.5 Booking Consistency

Google Calendar and PostgreSQL are separate systems. The implementation
must account for partial failures.

Recommended approach:

-   Database-backed booking request.
-   Booking operation identifier.
-   Slot reservation or locking.
-   Calendar event creation.
-   Database status update.
-   Reconciliation of incomplete operations.

Suggested appointment statuses:

-   `PENDING`
-   `CONFIRMED`
-   `CANCELLED`
-   `FAILED`
-   `REQUIRES_RECONCILIATION`

------------------------------------------------------------------------

# 9. Database Architecture

## 9.1 Database Selection

PostgreSQL is the primary persistent database.

SQLite may be used for isolated local experiments, but PostgreSQL must
be used for integration and production testing.

## 9.2 Database Entities

### Patients

-   `patient_id`
-   `full_name`
-   `phone_number`
-   `created_at`
-   `updated_at`

### Doctors

-   `doctor_id`
-   `doctor_name`
-   `specialization`
-   `calendar_id`
-   `timezone`
-   `active_status`

### Appointments

-   `appointment_id`
-   `patient_id`
-   `doctor_id`
-   `appointment_date`
-   `start_time`
-   `end_time`
-   `appointment_type`
-   `status`
-   `calendar_event_id`
-   `idempotency_key`
-   `created_at`
-   `updated_at`

### Conversations

-   `conversation_id`
-   `patient_id`
-   `session_id`
-   `started_at`
-   `ended_at`
-   `conversation_status`
-   `transcript_reference`

### Conversation Events

-   `event_id`
-   `conversation_id`
-   `event_type`
-   `event_data`
-   `timestamp`

### Evaluation Runs

-   `evaluation_run_id`
-   `agent_version`
-   `prompt_version`
-   `model_configuration`
-   `execution_status`
-   `started_at`
-   `completed_at`

### Evaluation Results

-   `evaluation_result_id`
-   `evaluation_run_id`
-   `scenario_id`
-   `execution_status`
-   `task_completion`
-   `tool_accuracy`
-   `safety_result`
-   `latency_metrics`
-   `failure_category`

### Audit Logs

-   `audit_id`
-   `actor`
-   `action`
-   `resource_type`
-   `resource_id`
-   `timestamp`
-   `result`

## 9.3 Data Separation

Patient information must remain separate from evaluation fixtures.

Evaluation scenarios must use synthetic patient information.

Production transcripts must not automatically become evaluation data
without an approved, privacy-preserving process.

------------------------------------------------------------------------

# 10. Evaluation and Testing Platform

## 10.1 Strategic Importance

The evaluation platform is a core product component.

It is developed alongside the voice agent, with its own architecture,
database entities, execution pipeline, and dashboard.

Its purpose is to continuously determine whether the agent:

-   Understands the patient.
-   Collects correct information.
-   Maintains conversational context.
-   Selects appropriate tools.
-   Uses tools with correct arguments.
-   Handles unavailable appointments.
-   Completes actual booking operations.
-   Communicates accurate results.
-   Follows safety requirements.

The evaluation system must inspect both conversational behavior and
application outcomes.

## 10.2 Evaluation Architecture

``` text
EVALUATION DASHBOARD
        |
        v
TEST SCENARIO MANAGER
        |
        v
SIMULATED PATIENT
        |
        v
TEST EXECUTION ENGINE
        |
        v
LIVEKIT AGENT SESSION
        |
        v
CUSTOM PYTHON AGENT
        |
        v
AGENT TOOLS
        |
        v
TEST DATABASE AND CALENDAR
        |
        v
EXECUTION TRACE COLLECTOR
        |
        v
EVALUATION ENGINE
        |
        +---- DETERMINISTIC ASSERTIONS
        |
        +---- LLM-BASED CONVERSATION JUDGE
        |
        v
FINAL EVALUATION REPORT
```

## 10.3 Evaluation Layers

The system contains five evaluation layers.

### Layer 1: Unit Testing

Tests individual components.

Examples:

-   Intent extraction.
-   Date extraction.
-   Time extraction.
-   Required-field validation.
-   State transitions.
-   Tool argument validation.
-   Calendar response handling.

Framework: Pytest.

These tests should use deterministic inputs and expected outputs.

### Layer 2: Tool Evaluation

Verifies whether the agent correctly invokes application tools.

Example expected call:

``` python
check_availability(
    doctor_id="DOC-001",
    appointment_date="2026-11-03",
    preferred_time="11:00"
)
```

The evaluator checks:

-   Whether the correct tool was called.
-   Whether required arguments were supplied.
-   Whether arguments were correct.
-   Whether the tool was called at the appropriate point.
-   Whether the agent correctly interpreted the result.

### Layer 3: Conversation Simulation

An LLM-based simulated patient interacts with the actual agent.

Each scenario defines:

-   Patient persona.
-   Initial request.
-   Information available to the patient.
-   Information to reveal only when asked.
-   Expected conversation behavior.
-   Expected final outcome.

The simulated patient must not reveal every piece of information
immediately. It should behave like a real caller.

### Layer 4: Final-State Evaluation

This is mandatory.

The system inspects actual application state.

Example expected result:

``` json
{
  "appointment_status": "CONFIRMED",
  "doctor_id": "DOC-001",
  "appointment_date": "2026-11-03",
  "appointment_time": "12:30"
}
```

Actual database and calendar state must be compared against the expected
result.

A successful LLM judge verdict cannot override an incorrect database or
calendar state.

### Layer 5: Audio Evaluation

The complete voice pipeline must be tested using audio.

Evaluate:

-   Speech recognition.
-   Transcription accuracy.
-   Voice quality.
-   Response latency.
-   Turn detection.
-   Interruptions.
-   Background noise.
-   Accent handling.
-   Speech output completeness.

Text simulations are used for frequent logic testing. Audio simulations
test the complete STT-LLM-TTS pipeline.

------------------------------------------------------------------------

# 11. Simulated Patient System

## 11.1 Purpose

The simulated patient is an independent AI-based testing participant.

It must not share the agent's internal conversation state or simply
imitate expected agent responses.

Its role is to initiate and maintain realistic conversations.

## 11.2 Patient Simulation Configuration

Each simulated patient should have:

-   Patient identity.
-   Communication style.
-   Appointment objective.
-   Available information.
-   Hidden information.
-   Preferred appointment.
-   Alternative preferences.
-   Conversation behavior.
-   Completion condition.

## 11.3 Simulation Behaviors

The simulated patient must support:

1.  Providing information incrementally.
2.  Providing incomplete information.
3.  Correcting previously supplied information.
4.  Changing appointment preferences.
5.  Asking unrelated questions.
6.  Rejecting alternatives.
7.  Accepting alternatives.
8.  Providing ambiguous dates.
9.  Interrupting the agent.
10. Ending conversations unexpectedly.

## 11.4 Scenario Isolation

Every simulation must execute in an isolated test environment.

The system must ensure:

-   No real patient records are modified.
-   No real appointments are created.
-   No real notifications are sent.
-   No production calendar events are affected.
-   Test data is cleaned up or retained according to test policy.

LiveKit simulation context should provide scenario-specific test data to
the agent.

------------------------------------------------------------------------

# 12. Evaluation Scenario Library

The initial release must include a committed scenario suite.

## Category A: Successful Booking

-   **TC-001:** Patient provides all information in one turn.
-   **TC-002:** Patient provides information incrementally.
-   **TC-003:** Patient requests a specific doctor and time.
-   **TC-004:** Patient accepts a suggested appointment.

## Category B: Missing Information

-   **TC-005:** Patient does not provide their name.
-   **TC-006:** Patient does not provide contact information.
-   **TC-007:** Patient does not specify a preferred time.
-   **TC-008:** Patient provides ambiguous appointment information.

## Category C: Unavailable Appointments

-   **TC-009:** Requested slot is unavailable.
-   **TC-010:** Patient accepts the first alternative.
-   **TC-011:** Patient rejects all alternatives.
-   **TC-012:** Patient requests another date.
-   **TC-013:** Slot becomes unavailable before final booking.

## Category D: Conversation Management

-   **TC-014:** Patient changes doctor preference.
-   **TC-015:** Patient changes appointment date.
-   **TC-016:** Patient corrects their name.
-   **TC-017:** Patient provides previously requested information again.
-   **TC-018:** Patient asks an unrelated question during booking.

## Category E: Backend Failures

-   **TC-019:** Google Calendar API unavailable.
-   **TC-020:** Database temporarily unavailable.
-   **TC-021:** Calendar event creation fails.
-   **TC-022:** Duplicate booking request.
-   **TC-023:** Database persistence fails after calendar event
    creation.
-   **TC-024:** Agent connection is interrupted.

## Category F: Safety

-   **TC-025:** Patient requests a diagnosis.
-   **TC-026:** Patient requests medication recommendations.
-   **TC-027:** Patient describes an emergency.
-   **TC-028:** Patient asks the agent to ignore its restrictions.
-   **TC-029:** Patient requests another patient's information.

## Category G: Audio Quality

-   **TC-030:** Background noise.
-   **TC-031:** Patient speaks slowly.
-   **TC-032:** Patient speaks rapidly.
-   **TC-033:** Patient interrupts the agent.
-   **TC-034:** Patient uses an unfamiliar pronunciation of a doctor's
    name.
-   **TC-035:** Patient provides numbers in multiple segments.

These scenarios form the initial evaluation baseline and must be
expanded as new failure patterns are identified.

------------------------------------------------------------------------

# 13. Evaluation Metrics

## 13.1 Task Completion Rate

Percentage of scenarios in which the expected task is completed
correctly.

`Task Completion Rate = Successfully completed scenarios / Total valid scenarios × 100`

## 13.2 Tool Accuracy

Measures whether the agent selected and executed the correct tools with
correct arguments.

## 13.3 Information Extraction Accuracy

Measures the accuracy of extracted patient and appointment information.

## 13.4 Booking Accuracy

Measures whether the actual booking matches the expected patient,
doctor, date, time, and status.

## 13.5 Conversation Quality

Measures:

-   Relevance.
-   Clarity.
-   Naturalness.
-   Context retention.
-   Appropriate clarification.
-   Conciseness.

## 13.6 Safety Compliance

Measures whether the agent follows approved restrictions and escalation
procedures.

Safety-critical failures must be reported separately and cannot be
hidden by an overall average score.

## 13.7 Latency

Measure:

-   User speech completion to first agent audio.
-   STT processing time.
-   LLM response time.
-   TTS generation time.
-   Tool execution time.
-   Total interaction latency.

## 13.8 Regression Detection

Every prompt, model, or business-logic change must be evaluated against
the committed baseline.

The system must identify whether a new change improves one metric while
degrading another.

------------------------------------------------------------------------

# 14. Evaluation Dashboard

## 14.1 Dashboard Purpose

The evaluation dashboard provides a central interface for inspecting
agent quality and reliability.

## 14.2 Dashboard Sections

### Overview

Display:

-   Total test runs.
-   Total scenarios.
-   Passed scenarios.
-   Failed scenarios.
-   Task completion rate.
-   Booking accuracy.
-   Safety failures.
-   Average latency.

### Scenario Management

Allow users to:

-   View test scenarios.
-   Create scenarios.
-   Edit scenarios.
-   Categorize scenarios.
-   Activate or deactivate scenarios.
-   Run individual scenarios.
-   Execute complete test suites.

### Execution Monitoring

Display:

-   Current execution status.
-   Active simulation count.
-   Completed scenarios.
-   Failed scenarios.
-   Execution duration.

### Conversation Inspector

For each test, show:

-   Simulated patient messages.
-   Agent responses.
-   Transcripts.
-   Tool calls.
-   Tool arguments.
-   Tool responses.
-   State transitions.
-   Final database state.

### Evaluation Results

Show:

-   Pass/fail status.
-   Expected result.
-   Actual result.
-   Evaluation explanation.
-   Failure category.
-   Related execution trace.

### Regression Comparison

Compare:

-   Previous agent version.
-   Current agent version.
-   Prompt changes.
-   Model changes.
-   Scenario results.
-   Performance differences.

### Reports

Generate downloadable evaluation reports in JSON and CSV formats.

------------------------------------------------------------------------

# 15. Functional Requirements

  ID       Requirement                                   Priority
  -------- --------------------------------------------- ----------
  FR-001   Establish browser-based voice communication   Critical
  FR-002   Maintain real-time agent sessions             Critical
  FR-003   Transcribe patient speech                     Critical
  FR-004   Generate natural voice responses              Critical
  FR-005   Identify patient intent                       Critical
  FR-006   Extract structured appointment information    Critical
  FR-007   Maintain conversation state                   Critical
  FR-008   Detect missing information                    Critical
  FR-009   Ask relevant follow-up questions              Critical
  FR-010   Retrieve doctor information                   High
  FR-011   Check calendar availability                   Critical
  FR-012   Suggest alternative slots                     Critical
  FR-013   Obtain patient confirmation                   Critical
  FR-014   Create calendar events                        Critical
  FR-015   Verify booking success                        Critical
  FR-016   Persist patient information                   Critical
  FR-017   Persist appointment information               Critical
  FR-018   Maintain conversation records                 High
  FR-019   Generate simulated patients                   Critical
  FR-020   Execute automated simulations                 Critical
  FR-021   Verify actual database outcomes               Critical
  FR-022   Evaluate tool execution                       Critical
  FR-023   Evaluate conversation quality                 High
  FR-024   Evaluate voice performance                    High
  FR-025   Maintain evaluation history                   High
  FR-026   Display evaluation dashboard                  High
  FR-027   Compare agent versions                        High
  FR-028   Support appointment cancellation              Medium
  FR-029   Support rescheduling                          Medium

------------------------------------------------------------------------

# 16. Non-Functional Requirements

## 16.1 Performance

Initial engineering targets:

-   Voice interaction should feel responsive.
-   Target median response latency should be below one second where
    practical.
-   Booking operations must return clear success or failure states.
-   Dashboard queries must remain responsive as evaluation history
    grows.

Latency must be measured at the audio level, not inferred from LLM
generation time alone.

## 16.2 Reliability

The system must:

-   Recover from temporary API failures.
-   Avoid duplicate bookings.
-   Preserve completed operations.
-   Handle incomplete conversations.
-   Maintain session isolation.
-   Log failed operations.
-   Support controlled retries.

## 16.3 Scalability

The architecture must support:

-   Multiple concurrent patient sessions.
-   Multiple doctors.
-   Multiple clinic calendars.
-   Concurrent evaluation runs.
-   Additional communication channels.

## 16.4 Maintainability

The application must use:

-   Modular Python packages.
-   Typed interfaces.
-   Pydantic schemas.
-   Dependency injection.
-   Database migrations.
-   Automated tests.
-   Version-controlled configurations.

------------------------------------------------------------------------

# 17. Security, Privacy and Safety

Because the application operates in a healthcare environment, privacy
and security are core requirements.

## 17.1 Data Protection

The system must:

-   Collect only necessary patient information.
-   Protect sensitive data in transit and at rest.
-   Restrict access to patient records.
-   Avoid exposing personal information in application logs.
-   Apply retention policies to transcripts and recordings.
-   Obtain appropriate consent before recording or retaining
    conversations.
-   Separate testing data from production data.

## 17.2 Authentication and Authorization

Implement:

-   Secure administrator authentication.
-   Role-based access control.
-   Protected backend endpoints.
-   Secure OAuth token storage.
-   Environment-based secret management.

## 17.3 Agent Safety

The agent must:

-   Identify itself as an AI receptionist.
-   Avoid presenting itself as a doctor.
-   Avoid providing independent medical diagnoses.
-   Avoid inventing clinical information.
-   Follow approved emergency escalation instructions.
-   Avoid disclosing information about other patients.

## 17.4 Auditability

Important operations must produce audit records.

Examples:

-   Patient record created.
-   Appointment checked.
-   Appointment booked.
-   Appointment cancelled.
-   Calendar operation failed.
-   Administrator modified doctor availability.

The clinic must approve applicable privacy, retention, hosting, and
regulatory requirements before using real patient data.

------------------------------------------------------------------------

# 18. API and Service Boundaries

The architecture maintains a clear separation between agent reasoning
and backend operations.

## 18.1 Agent Layer

Responsible for:

-   Understanding requests.
-   Maintaining context.
-   Choosing appropriate tools.
-   Communicating results.

## 18.2 Backend Layer

Responsible for:

-   Validating requests.
-   Managing patient records.
-   Managing appointment records.
-   Enforcing booking rules.
-   Handling calendar integration.
-   Returning structured responses.

## 18.3 Evaluation Layer

Responsible for:

-   Creating scenarios.
-   Running simulations.
-   Collecting execution traces.
-   Verifying outcomes.
-   Calculating metrics.
-   Producing reports.

## 18.4 Initial API Endpoints

### Patient and Appointment Operations

``` text
POST /api/v1/patients
GET  /api/v1/patients/{patient_id}

GET  /api/v1/doctors
GET  /api/v1/doctors/{doctor_id}

POST /api/v1/appointments/availability
POST /api/v1/appointments
GET  /api/v1/appointments/{appointment_id}

POST /api/v1/appointments/{appointment_id}/cancel
POST /api/v1/appointments/{appointment_id}/reschedule
```

### Evaluation Operations

``` text
POST /api/v1/evaluations/runs
GET  /api/v1/evaluations/runs
GET  /api/v1/evaluations/runs/{run_id}
GET  /api/v1/evaluations/runs/{run_id}/results

POST /api/v1/evaluations/scenarios
GET  /api/v1/evaluations/scenarios
POST /api/v1/evaluations/scenarios/{scenario_id}/run
```

API contracts must be defined using Pydantic models and documented
through OpenAPI.

------------------------------------------------------------------------

# 19. Repository Structure

``` text
clinical-voice-agent/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   └── services/
│   └── package.json
│
├── backend/
│   ├── agent/
│   │   ├── voice_agent.py
│   │   ├── prompts.py
│   │   ├── conversation_manager.py
│   │   ├── state_manager.py
│   │   └── guardrails.py
│   │
│   ├── services/
│   │   ├── patient_service.py
│   │   ├── appointment_service.py
│   │   ├── calendar_service.py
│   │   └── confirmation_service.py
│   │
│   ├── tools/
│   │   ├── availability.py
│   │   ├── booking.py
│   │   ├── cancellation.py
│   │   └── rescheduling.py
│   │
│   ├── database/
│   │   ├── models.py
│   │   ├── connection.py
│   │   └── repositories.py
│   │
│   ├── api/
│   │   ├── routes/
│   │   └── schemas/
│   │
│   └── main.py
│
├── evaluation/
│   ├── scenarios/
│   ├── simulators/
│   │   └── simulated_patient.py
│   ├── evaluators/
│   │   ├── conversation_evaluator.py
│   │   ├── tool_evaluator.py
│   │   ├── task_evaluator.py
│   │   └── safety_evaluator.py
│   ├── metrics/
│   ├── reporting/
│   └── runner.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── simulation/
│   └── end_to_end/
│
├── migrations/
├── config/
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

The structure is a starting contract. Modules may be reorganized as
implementation progresses, provided architectural boundaries remain
intact.

------------------------------------------------------------------------

# 20. Development Roadmap

Development follows eight implementation phases.

## Phase 1: Project Foundation

Tasks:

-   Create repository.
-   Configure Python environment.
-   Initialize LiveKit project.
-   Create React frontend.
-   Configure FastAPI.
-   Establish environment configuration.
-   Configure Docker.
-   Define shared interfaces.

**Deliverable:** A working project foundation with frontend, backend,
and LiveKit connectivity.

## Phase 2: Voice Agent

Tasks:

-   Implement LiveKit agent entrypoint.
-   Configure STT.
-   Configure LLM.
-   Configure ElevenLabs TTS.
-   Implement conversation lifecycle.
-   Implement real-time transcription.
-   Handle interruptions.
-   Implement browser voice interface.

**Deliverable:** A working browser-based conversational voice agent.

## Phase 3: Agent Intelligence

Tasks:

-   Design system prompt.
-   Implement intent identification.
-   Implement structured information extraction.
-   Implement conversation manager.
-   Implement deterministic state machine.
-   Implement missing-information handling.
-   Implement safety restrictions.

**Deliverable:** A conversational clinical receptionist capable of
collecting appointment information.

## Phase 4: Backend and Database

Tasks:

-   Implement PostgreSQL.
-   Define database models.
-   Configure SQLAlchemy.
-   Configure Alembic.
-   Implement patient service.
-   Implement doctor service.
-   Implement appointment service.
-   Implement audit logging.

**Deliverable:** Persistent backend infrastructure.

## Phase 5: Google Calendar

Tasks:

-   Configure OAuth.
-   Connect doctor calendars.
-   Implement free/busy queries.
-   Implement availability calculation.
-   Implement alternative slots.
-   Implement appointment creation.
-   Implement cancellation and rescheduling.
-   Implement booking reconciliation.

**Deliverable:** An operational appointment management system.

## Phase 6: Evaluation Infrastructure

Tasks:

-   Integrate LiveKit unit-testing capabilities.
-   Implement scenario management.
-   Develop simulated patient.
-   Implement text simulations.
-   Implement deterministic final-state grading.
-   Implement tool evaluation.
-   Implement conversation evaluation.
-   Implement evaluation result persistence.

**Deliverable:** A working automated evaluation engine.

## Phase 7: Evaluation Dashboard and Audio Testing

Tasks:

-   Develop dashboard.
-   Implement execution monitoring.
-   Implement conversation inspector.
-   Implement regression comparison.
-   Implement audio simulations.
-   Measure speech recognition accuracy.
-   Measure voice latency.
-   Generate evaluation reports.

**Deliverable:** A complete testing and evaluation platform.

## Phase 8: End-to-End Validation

Tasks:

-   Run complete booking scenarios.
-   Test calendar conflicts.
-   Test concurrent requests.
-   Test API failures.
-   Test safety scenarios.
-   Test audio conditions.
-   Validate database integrity.
-   Perform security review.
-   Prepare deployment.

**Deliverable:** A validated clinical receptionist prototype.

------------------------------------------------------------------------

# 21. Definition of Done

The first release is not considered complete merely because the agent
can communicate.

The following acceptance criteria must be satisfied.

## Voice System

-   Patient can initiate a browser-based conversation.
-   Agent can receive and respond to audio.
-   Transcription works reliably in supported languages.
-   Interruptions and conversation termination are handled.

## Agent Intelligence

-   Agent identifies supported intents.
-   Required information is collected.
-   Missing information is handled correctly.
-   Conversation context is preserved.
-   Agent follows its approved restrictions.

## Appointment Management

-   Agent retrieves actual doctor availability.
-   Unavailable appointments produce alternatives.
-   Patient confirmation is obtained.
-   Booking creates the correct calendar event.
-   Database contains the corresponding appointment.
-   Duplicate bookings are prevented.
-   Failed operations are reported accurately.

## Evaluation System

-   Test scenarios can be created and executed.
-   Simulated patients can interact with the real agent.
-   Tool calls are inspected.
-   Database outcomes are verified.
-   Calendar outcomes are verified.
-   Conversation quality is evaluated.
-   Safety failures are identified.
-   Evaluation results are persisted.
-   Previous agent versions can be compared.

## Overall Release Criteria

The initial release should target:

-   At least 95% task completion on the approved core booking scenario
    suite.
-   At least 98% correct booking outcomes on valid booking tests.
-   100% pass rate on critical safety and booking-integrity tests.
-   No duplicate appointment creation in the defined concurrency test
    suite.
-   No false booking confirmations.
-   Successful execution of all mandatory integration tests.

These are proposed release gates, not measured performance claims. They
must be validated using a sufficiently large, representative test suite.

------------------------------------------------------------------------

# 22. Risks and Mitigation

  -----------------------------------------------------------------------
  Risk                                Mitigation
  ----------------------------------- -----------------------------------
  Incorrect speech recognition        Test multiple STT providers and use
                                      confirmation for critical fields

  Incorrect date interpretation       Normalize dates using a controlled
                                      timezone and test clock

  LLM hallucination                   Ground responses in backend data

  Duplicate appointments              Idempotency and booking locks

  Calendar inconsistency              Reconciliation workflow

  Voice latency                       Streaming and per-stage profiling

  Poor simulated-patient behavior     Scenario validation and independent
                                      assertions

  LLM judge inconsistency             Deterministic assertions for
                                      critical outcomes

  Prompt regressions                  Versioned prompts and regression
                                      testing

  Sensitive data exposure             Data minimization and access
                                      controls

  API outages                         Retries, timeouts, and graceful
                                      failure handling
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# 23. Future Extensions

Once the browser-based system is validated, the architecture can support
additional channels.

## Phone Integration

Twilio or LiveKit SIP integration can connect incoming calls to the
existing voice agent.

The booking service and conversation logic should remain unchanged.

## WhatsApp Integration

WhatsApp Business API can deliver:

-   Appointment confirmations.
-   Appointment reminders.
-   Cancellation notifications.
-   Rescheduling information.

## Advanced Evaluation

Future evaluation capabilities may include:

-   Multilingual testing.
-   Accent-specific benchmarking.
-   Adversarial conversation testing.
-   Load testing.
-   Long-duration session testing.
-   Automated failure-to-scenario generation.
-   Production monitoring.
-   Model and provider comparisons.

------------------------------------------------------------------------

# 24. Technical Implementation Principles

The following principles are mandatory throughout development.

1.  Keep voice infrastructure independent from business logic.
2.  Keep agent reasoning independent from appointment execution.
3.  Use deterministic backend services for critical operations.
4.  Use structured data rather than unvalidated conversational text.
5.  Make evaluation a first-class subsystem.
6.  Verify actual application state rather than trusting conversation
    transcripts.
7.  Keep testing and production environments isolated.
8.  Version prompts, models, and evaluation scenarios.
9.  Make external integrations replaceable.
10. Never allow an unverified operation to be communicated as
    successful.

------------------------------------------------------------------------

# 25. Final Product Definition

The initial product is a browser-based AI clinical receptionist with
integrated appointment scheduling and an independent automated
evaluation platform.

  -----------------------------------------------------------------------
  Component                           Technology
  ----------------------------------- -----------------------------------
  Patient interface                   React + WebRTC + LiveKit

  Voice infrastructure                LiveKit Agents

  Conversational intelligence         Custom Python agent

  Reasoning                           OpenAI LLM

  Speech processing                   Provider-based STT

  Voice generation                    ElevenLabs

  Backend                             FastAPI

  Scheduling                          Google Calendar API

  Persistence                         PostgreSQL

  Evaluation                          LiveKit Agent Simulations + Custom
                                      Python Evaluation Engine

  Monitoring                          Evaluation Dashboard
  -----------------------------------------------------------------------

The defining feature of the product will not simply be its ability to
conduct voice conversations.

It will be its ability to demonstrate, through repeatable automated
evaluation, that conversations result in correct, safe, and verified
administrative outcomes.

------------------------------------------------------------------------

# 26. Technical References and Documentation

The following official documentation should be treated as the primary
technical reference set during development. Provider APIs and
documentation evolve, so verify current SDK versions and supported
features when implementing each integration.

## 26.1 LiveKit: Voice Infrastructure

-   [LiveKit Agents Documentation](https://docs.livekit.io/agents/) ---
    Overall architecture, Python agents, integrations, and
    communication.
-   [LiveKit Python Voice AI
    Quickstart](https://docs.livekit.io/agents/start/voice-ai/) ---
    Initial project setup and first working agent.
-   [LiveKit Agent
    Sessions](https://docs.livekit.io/agents/logic/sessions/) ---
    Session management, pipeline orchestration, and tools.
-   [LiveKit Pipeline
    Types](https://docs.livekit.io/agents/models/pipelines/) ---
    Comparison of cascaded and realtime voice architectures.
-   [LiveKit Job Lifecycle](https://docs.livekit.io/agents/server/job/)
    --- Agent execution and session lifecycle.
-   [LiveKit Pipeline Nodes and
    Hooks](https://docs.livekit.io/agents/logic/nodes/) --- Customizing
    the voice processing pipeline.

**Implementation note:** Start with the cascaded STT → LLM → TTS
architecture. It provides modularity, observability, and the ability to
test each stage independently.

## 26.2 Evaluation Infrastructure

-   [LiveKit Testing Overview](https://docs.livekit.io/testing/) ---
    Testing capabilities.
-   [LiveKit Agent
    Simulations](https://docs.livekit.io/testing/simulations/) ---
    Simulated conversations with an agent.
-   [LiveKit Unit Testing](https://docs.livekit.io/testing/unit-tests/)
    --- Unit testing support.
-   [LiveKit Scenario
    Sets](https://docs.livekit.io/testing/simulations/scenario-sets/)
    --- Organizing simulation scenarios.
-   [LiveKit Agent Testing
    CLI](https://docs.livekit.io/reference/developer-tools/livekit-cli/agent/testing/)
    --- Running agent tests.

LiveKit Agent Simulations are particularly relevant. They provide a
simulated user, an actual agent execution, and evaluation capabilities.
Custom final-state verification should be added so the system checks
real appointment records rather than relying only on a conversational
judge.

**Implementation decision:** Build the custom evaluation dashboard and
deterministic graders around LiveKit's simulation capabilities. Do not
unnecessarily reinvent the entire simulation infrastructure.

## 26.3 OpenAI: Speech and Reasoning

-   [OpenAI
    Speech-to-Text](https://developers.openai.com/api/docs/guides/transcription)
    --- Transcription workflows.
-   [OpenAI Audio and Speech
    Documentation](https://developers.openai.com/api/docs/guides/speech-to-text)
    --- Audio processing guidance.
-   [OpenAI Voice
    Agents](https://developers.openai.com/api/docs/guides/voice-agents)
    --- Voice agent architecture and design considerations.
-   [OpenAI Realtime
    Conversations](https://developers.openai.com/api/docs/guides/realtime-conversations)
    --- Speech-to-speech alternative.

The Whisper implementation should not be treated as a fixed dependency.
Select the transcription model through benchmarking and verify current
model availability before implementation.

## 26.4 ElevenLabs: Voice Generation

-   [ElevenLabs Streaming
    TTS](https://elevenlabs.io/docs/eleven-api/guides/how-to/text-to-speech/streaming)
    --- Streaming text-to-speech.
-   [ElevenLabs Streaming API
    Reference](https://elevenlabs.io/docs/api-reference/streaming) ---
    API implementation details.

Benchmark streaming voice generation, pronunciation accuracy, and
response latency before selecting a voice.

## 26.5 Google Calendar API

-   [Google Calendar OAuth and
    Permissions](https://developers.google.com/workspace/calendar/api/auth)
    --- Authorization.
-   [Google Calendar FreeBusy
    API](https://developers.google.com/workspace/calendar/api/v3/reference/freebusy/query)
    --- Calendar availability.
-   [Google Calendar Create
    Events](https://developers.google.com/workspace/calendar/api/guides/create-events)
    --- Event creation.
-   [Google Calendar Events Insert
    API](https://developers.google.com/workspace/calendar/api/v3/reference/events/insert)
    --- Event insertion reference.

These are the primary references for availability checking,
authorization, and appointment creation.

## 26.6 Backend and Database

-   [FastAPI Documentation](https://fastapi.tiangolo.com/learn/) ---
    Backend development.
-   [FastAPI
    Security](https://fastapi.tiangolo.com/tutorial/security/first-steps/)
    --- Authentication and security.
-   [FastAPI SQL Database
    Integration](https://fastapi.tiangolo.com/tutorial/sql-databases/)
    --- Database integration.
-   [SQLAlchemy Documentation](https://docs.sqlalchemy.org/) --- ORM and
    database access.
-   [Alembic Documentation](https://alembic.sqlalchemy.org/) ---
    Database migrations.
-   [PostgreSQL Documentation](https://www.postgresql.org/docs/) ---
    Database administration and SQL.

------------------------------------------------------------------------

# 27. Recommended Initial Development Sequence

The first development cycle should establish both the voice agent and
its evaluation loop.

  -----------------------------------------------------------------------
  Order                   Development task        Expected outcome
  ----------------------- ----------------------- -----------------------
  1                       Repository and          Working development
                          environment setup       environment

  2                       LiveKit Python starter  First working voice
                                                  session

  3                       React voice interface   Browser-based
                                                  communication

  4                       Basic custom agent      Natural conversation

  5                       Agent state machine     Controlled conversation
                                                  flow

  6                       PostgreSQL and FastAPI  Persistent backend

  7                       Google Calendar         Real appointment
                          integration             scheduling

  8                       First simulated patient Automated conversation
                                                  testing

  9                       Deterministic evaluator Verified booking
                                                  outcomes

  10                      Evaluation dashboard    Central testing
                                                  interface
  -----------------------------------------------------------------------

**First milestone:** A working LiveKit agent with a simulated-patient
test running against it, even before calendar integration.

This establishes the development and evaluation cycle early. Once it
works, every new capability can be developed with corresponding tests.

------------------------------------------------------------------------

# End of Product Requirements Document
