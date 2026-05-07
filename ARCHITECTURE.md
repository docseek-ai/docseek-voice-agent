# Architecture — DocSeek Medical Voice Agent

High-level design of the medical front desk voice agent.

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Patient (Phone Call)                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                    WebRTC Audio
                         │
        ┌────────────────▼─────────────────┐
        │      LiveKit (Signaling)         │
        │  - Room management               │
        │  - SFU (media distribution)      │
        │  - Call recording                │
        └────────────────┬─────────────────┘
                         │
        ┌────────────────▼──────────────────────────────────────┐
        │   Voice Agent (STT → LLM → TTS Pipeline)             │
        │                                                       │
        │  ┌──────────────────────────────────────────────┐    │
        │  │  Speech-to-Text (Deepgram or Google)        │    │
        │  │  Audio → Text (real-time streaming)         │    │
        │  └────────────┬─────────────────────────────────┘    │
        │               │                                       │
        │  ┌────────────▼──────────────────────────────────┐   │
        │  │  Large Language Model (OpenAI GPT-4o-mini)   │   │
        │  │  - Medical system prompt                     │   │
        │  │  - Conversation context management           │   │
        │  │  - Function calling for appointments         │   │
        │  └────────────┬──────────────────────────────────┘   │
        │               │                                       │
        │  ┌────────────▼──────────────────────────────────┐   │
        │  │  Text-to-Speech (OpenAI or Google)           │   │
        │  │  Text → Audio (natural voice)                │   │
        │  └──────────────────────────────────────────────┘   │
        │                                                       │
        │  Local State:                                        │
        │  - Conversation history (ChatContext)               │
        │  - Patient intake form responses                    │
        │  - Temporary appointment details                    │
        └────────────────┬──────────────────────────────────┘
                         │
        ┌────────────────▼──────────────────┐
        │  Medical Clinic Logic             │
        │  - Appointment scheduling         │
        │  - Patient intake questions       │
        │  - Availability checking          │
        │  - Confirmation handling          │
        └────────────────┬──────────────────┘
                         │
        ┌────────────────▼──────────────────┐
        │  Persistent Storage               │
        │  - Patient records (PostgreSQL)   │
        │  - Appointments (PostgreSQL)      │
        │  - Call session logs              │
        │  - Analytics                      │
        └───────────────────────────────────┘
```

## Core Components

### 1. **Agent Entry Point** (`src/agent.py`)

- **Responsibility**: Bootstrap the voice pipeline, manage session lifecycle
- **Key Functions**:
  - `entrypoint(ctx)`: Main handler for incoming calls
  - `prewarm_process()`: Pre-download models before agent starts
- **Flow**:
  1. Receive incoming room session from LiveKit
  2. Initialize STT/LLM/TTS pipeline
  3. Start recording and processing
  4. Manage conversation until session ends

### 2. **Configuration** (`src/docseek_voice_agent/config.py`)

- Pydantic-based settings loader
- Reads from `.env.local`
- Single source of truth for credentials and clinic info
- Supports multiple environments (local, dev, prod)

### 3. **Clinic Logic** (`src/docseek_voice_agent/clinic_logic.py`)

Three main classes:

#### **MedicalAgentPrompt**
- System prompt templates tailored for medical receptionists
- Defines agent behavior: warm, professional, HIPAA-aware
- Regenerated per session with clinic name and context

#### **AppointmentHandler**
- Manages appointment availability and scheduling
- Mock slot generation (extendable to real calendar APIs)
- Appointment confirmation and cancellation
- Example:
  ```python
  handler = AppointmentHandler()
  result = await handler.schedule_appointment(
      patient_name="John Doe",
      phone="+1-555-0123",
      preferred_date="2026-05-15",
      preferred_time="14:00",
      reason="Annual checkup"
  )
  ```

#### **PatientIntakeForm**
- Structured health history questionnaire
- Tracks completed questions
- Progressive disclosure (one question at a time)
- Questions:
  - Allergies
  - Current medications
  - Chronic conditions
  - Surgery history
  - Family history

### 4. **Database Models** (`src/docseek_voice_agent/database.py`)

SQLAlchemy ORM:

| Model | Purpose |
|-------|---------|
| `Patient` | Contact and demographics |
| `Appointment` | Scheduled appointments with confirmation |
| `PatientIntakeRecord` | Health history responses |
| `PhoneSession` | Call tracking and analytics |

Initialize once per deployment:
```python
from docseek_voice_agent.database import init_db
init_db()  # Creates tables
```

## Call Flow — Detailed

### Happy Path: Schedule Appointment

```
1. Patient calls → LiveKit routes to Agent → Agent wakes up
   
2. Agent (via LLM): "Hello! Thank you for calling. How can I help?"
   
3. Patient: "I need to schedule an appointment"
   
4. Agent analyzes intent, calls AppointmentHandler
   
5. Agent: "What's the reason for your visit?"
   
6. Patient: "Annual checkup"
   
7. Agent: "Great! What date works for you?"
   
8. Patient: "Next Tuesday at 2 PM"
   
9. Agent queries available_slots, finds a match
   
10. Agent: "Perfect! Let me confirm: John Doe, 555-0123, 
    Tuesday May 15 at 2 PM with Dr. Johnson. Correct?"
   
11. Patient: "Yes"
   
12. Agent calls appointment_handler.schedule_appointment()
   
13. Appointment saved to database with confirmation_id
   
14. Agent: "Appointment confirmed! Your confirmation number is APP-2026050701234.
    You'll receive an SMS reminder 24 hours before."
   
15. Session ends, call disconnected
```

### Branching: No Availability

```
7b. Agent queries available_slots for "May 15"
    → No 2 PM slot found
    
8b. Agent (LLM): "We don't have 2 PM on that day. 
    Available times are 10 AM, 2:30 PM, or 3:30 PM. 
    Which works for you?"
    
9b. Patient: "3:30 PM"
    
[Continue from step 9 onwards with corrected time]
```

## Real-Time Audio Processing

LiveKit Agents handles the complexity, but here's what happens:

1. **Audio Input**: Patient's microphone → LiveKit → Agent's RTC participant
2. **Speech-to-Text**: 
   - Audio chunked into frames
   - Sent to Deepgram (streaming)
   - Partial transcript returns in ~100ms
   - Final transcript when voice activity ends
3. **LLM Processing**:
   - Text fed to GPT-4o-mini
   - Medical system prompt provides context
   - Response generated token-by-token
   - Full response ready in ~500–1000ms
4. **Text-to-Speech**:
   - Generated text sent to OpenAI TTS
   - Synthesized audio returned
   - Audio queued and streamed back to patient
5. **Turn Management**:
   - Silero VAD detects when patient stops talking
   - EOUDetector prevents agent from interrupting mid-sentence
   - Natural conversation flow maintained

**Latency**: First response typically within 1–2 seconds (human-like).

## State Management

### Session State
Stored in memory during the call:

```python
{
    "chat_history": [  # Full conversation
        {"role": "system", "content": "You are a medical receptionist..."},
        {"role": "assistant", "content": "Hello! How can I help?"},
        {"role": "user", "content": "I need an appointment"},
        ...
    ],
    "patient_info": {
        "name": "John Doe",
        "phone": "+1-555-0123",
        "email": None,
        ...
    },
    "appointment_candidate": {
        "date": "2026-05-15",
        "time": "14:00",
        "reason": "checkup",
        ...
    },
    "intake_completed_questions": ["allergies", "medications"],
    ...
}
```

### Persistent State
Saved to database after session ends:

- Appointment record (with confirmation_id)
- Patient intake responses
- Call duration and outcome
- Transcript (optional, for audit)

## Error Handling & Fallbacks

### LLM Errors
If the LLM doesn't understand a patient request:
- Agent attempts to clarify
- Falls back to predefined menu ("Would you like to (1) schedule, (2) cancel, (3) speak with staff?")

### Appointment Booking Fails
- Agent provides clinic phone number for manual booking
- Logs the attempted booking for staff review

### Speech Recognition Fails
- Agent says "I didn't catch that. Could you repeat?"
- Silero VAD detects if patient is still speaking (doesn't interrupt)
- Retries up to 3 times, then offers phone number

### Database Connection Lost
- Agent continues conversation in memory
- Sends alert to clinic staff
- On session end, attempts to persist or queues for retry

## Integration Points

### Calendar Systems (Future)
```python
# Pseudo-code: integrate with Google Calendar, Outlook, etc.
class CalendarAdapter:
    async def get_availability(self, provider: str, date: str) -> List[TimeSlot]:
        # Query Google Calendar API for Dr. Johnson on May 15
        # Return available slots
```

### EHR/EMR Systems (Future)
```python
class EHRAdapter:
    async def lookup_patient(self, phone: str) -> PatientRecord:
        # Query Epic, Cerner, etc. for existing patient
    
    async def verify_insurance(self, patient_id: str) -> InsuranceInfo:
        # Real-time insurance verification
```

### SMS/Email (Future)
```python
class NotificationService:
    async def send_appointment_confirmation(self, appointment: Appointment):
        # Send SMS: "Appointment confirmed for Tue May 15 at 2 PM"
        # Send email with iCal attachment
```

## Deployment Architecture

### Local Development
```
Your Machine
├── LiveKit (Docker)
├── Agent Process (uv run python src/agent.py dev)
└── SQLite Database
```

### Production (LiveKit Cloud)
```
LiveKit Cloud (Managed)
├── Room/SFU
└── Agent Deployed via `lk agent create`

External Services
├── OpenAI API (LLM, TTS)
├── Deepgram API (STT)
└── PostgreSQL (Managed)
```

## Scaling Considerations

### Single Agent
- Handles one call at a time
- Concurrent calls = multiple agent instances

### Multiple Agents (Farm)
```
LoadBalancer (LiveKit)
├── Agent Pod 1 (Max 10 concurrent calls)
├── Agent Pod 2
└── Agent Pod N

All share:
├── PostgreSQL (appointments, patients)
└── Redis (session state, rate limiting)
```

## Testing Strategy

### Unit Tests
- `test_clinic_logic.py`: Logic isolated from LiveKit
- Appointment scheduling, intake form progression
- ~90% code coverage target

### Integration Tests (Future)
- Full call simulation with mock STT/TTS
- End-to-end booking flow
- Error scenarios

### Load Tests (Future)
- Concurrent call simulation
- Database connection pooling
- TTS/STT rate limits

## Security & Privacy

### HIPAA Compliance (Roadmap)
- [ ] Encrypt database at rest
- [ ] SFTP/TLS for all API calls
- [ ] Audit logging (who accessed what, when)
- [ ] Data retention policies (auto-delete old calls)
- [ ] De-identification for training/analytics

### Current Safeguards
- API keys in `.env.local` (never in code)
- No logging of sensitive patient data (names, phone redacted in logs)
- SQLite default (not production-grade; use PostgreSQL + encryption in prod)

---

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| **Python + LiveKit Agents** | Native async/await, type-safe, battle-tested framework |
| **OpenAI GPT-4o-mini** | Cheap, fast, good enough for routing (use GPT-4 for complex cases) |
| **Deepgram for STT** | Lower latency than Google, better accuracy for accents |
| **Pydantic for config** | Type validation, IDE support, minimal boilerplate |
| **SQLAlchemy** | ORM agnostic to db (SQLite local, PostgreSQL prod) |
| **Docker-ready** | One `docker build` deploys anywhere |

---

For implementation details, see individual module docstrings.
