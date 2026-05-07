# DocSeek MCP Server — Appointment & Patient Management

A Model Context Protocol (MCP) server that exposes the voice agent's database operations as tools. This allows the voice agent (and other Claude instances) to reliably manage appointments, patient records, and intake forms.

## Overview

The MCP server provides a clean abstraction over the database layer:

```
Voice Agent (LiveKit)
      ↓
   LLM Prompt
      ↓
   MCP Tools  ← Database operations (appointments, patients, intake)
      ↓
  SQLAlchemy ↔ PostgreSQL/SQLite
```

**Benefits:**
- 🔒 **Reliable**: Database operations are atomic and transactional
- 🛡️ **Safe**: Input validation, conflict detection, error handling
- 📊 **Auditable**: All operations logged; full appointment history
- 🔄 **Swappable**: Replace SQLite with PostgreSQL without changing agent code

## Running the Server

### Local (Development)

```bash
cd ~/Projects/docseek-voice-agent
uv sync
python -m docseek_voice_agent.mcp_server
```

This starts the MCP server on stdio. Connect from Claude Code or another MCP client.

### With Docker

```bash
docker run \
  -e DATABASE_URL=postgresql://user:pass@db:5432/docseek \
  -e LOG_LEVEL=info \
  docseek-voice-agent \
  python -m docseek_voice_agent.mcp_server
```

### Configuration

Set via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./docseek_voice.db` | Database connection string |
| `LOG_LEVEL` | `info` | Logging level (debug, info, warning, error) |

## Available Tools

### `get_available_slots`

Get available appointment slots for a date range.

**Parameters:**
- `start_date` (string, required): Date in YYYY-MM-DD format
- `end_date` (string, required): Date in YYYY-MM-DD format
- `provider` (string, optional): Filter by provider name

**Response:**
```json
{
  "available_slots": [
    {
      "date": "2026-05-08",
      "time": "09:00",
      "provider": "Dr. Sarah Johnson",
      "duration_minutes": 30
    }
  ],
  "total_available": 150
}
```

**Example:**
```
Get available slots for next week with Dr. Chen
→ start_date: 2026-05-08
→ end_date: 2026-05-14
→ provider: "Dr. Michael Chen"
```

---

### `book_appointment`

Book an appointment for a patient. Creates patient record if needed.

**Parameters:**
- `patient_name` (string, required): Full name
- `phone` (string, required): Phone number
- `appointment_date` (string, required): YYYY-MM-DD
- `appointment_time` (string, required): HH:MM (24-hour)
- `provider` (string, required): Provider name
- `reason` (string, required): Reason for visit
- `email` (string, optional): Email address

**Response:**
```json
{
  "success": true,
  "confirmation_id": "APT-20260507120000",
  "patient_name": "John Doe",
  "appointment_date": "2026-05-08",
  "appointment_time": "14:00",
  "provider": "Dr. Sarah Johnson",
  "reason": "Annual checkup"
}
```

**Errors:**
- Slot already booked: Returns `success: false` with error message
- Patient lookup fails: Returns error (patient must exist first)

---

### `cancel_appointment`

Cancel an existing appointment.

**Parameters:**
- `confirmation_id` (string, required): Appointment confirmation ID

**Response:**
```json
{
  "success": true,
  "confirmation_id": "APT-20260507120000",
  "status": "cancelled"
}
```

---

### `get_appointment`

Look up an appointment by confirmation ID.

**Parameters:**
- `confirmation_id` (string, required): Appointment confirmation ID

**Response:**
```json
{
  "success": true,
  "confirmation_id": "APT-20260507120000",
  "patient_name": "Jane Doe",
  "phone": "+1-555-9876",
  "appointment_date": "2026-05-08",
  "appointment_time": "10:00",
  "provider": "Dr. Michael Chen",
  "reason": "Follow-up visit",
  "status": "confirmed"
}
```

---

### `get_patient`

Look up patient information and appointment history.

**Parameters:**
- `phone` (string, required): Patient phone number

**Response:**
```json
{
  "success": true,
  "patient_id": 1,
  "name": "John Doe",
  "phone": "+1-555-0123",
  "email": "john@example.com",
  "recent_appointments": [
    {
      "confirmation_id": "APT-20260507120000",
      "date": "2026-05-08",
      "time": "14:00",
      "provider": "Dr. Sarah Johnson"
    }
  ]
}
```

---

### `save_patient_intake`

Save patient intake form responses (health history).

**Parameters:**
- `phone` (string, required): Patient phone number
- `allergies` (string, optional): Known allergies
- `current_medications` (string, optional): Current medications
- `chronic_conditions` (string, optional): Chronic conditions
- `surgery_history` (boolean, optional): Has had major surgery
- `family_history` (string, optional): Family medical history

**Response:**
```json
{
  "success": true,
  "patient_id": 1,
  "intake_completed": true
}
```

---

### `get_providers`

Get list of available providers at the clinic.

**Parameters:** None

**Response:**
```json
{
  "providers": [
    "Dr. Sarah Johnson",
    "Dr. Michael Chen",
    "Nurse Practitioner Emily Rodriguez"
  ]
}
```

## Usage in Voice Agent

The voice agent calls these tools automatically when the LLM determines they're needed:

```
Patient: "I'd like to book an appointment"

Agent (LLM): *intent: schedule*
  1. Call get_providers() → get list
  2. Ask patient which provider
  3. Patient: "Dr. Chen"
  4. Call get_available_slots(start_date, end_date, "Dr. Michael Chen")
  5. Present slots to patient
  6. Patient: "May 8 at 2 PM"
  7. Call book_appointment(...) → APT-20260507140000
  8. Confirm with patient
```

## Database Schema

The MCP server manages these tables:

### `patients`
- `id` (int, PK)
- `name` (string)
- `phone` (string, unique)
- `email` (string, nullable)
- `date_of_birth` (string, nullable)
- `insurance_provider` (string, nullable)
- `created_at` (datetime)
- `updated_at` (datetime)

### `appointments`
- `id` (int, PK)
- `confirmation_id` (string, unique)
- `patient_id` (int, FK)
- `patient_name` (string)
- `phone` (string)
- `appointment_date` (string)
- `appointment_time` (string)
- `provider` (string)
- `reason` (text)
- `status` (string) — `confirmed`, `cancelled`, `completed`, `no-show`
- `created_at` (datetime)
- `updated_at` (datetime)

### `patient_intake`
- `id` (int, PK)
- `patient_id` (int, FK)
- `appointment_id` (int, FK, nullable)
- `allergies` (text, nullable)
- `current_medications` (text, nullable)
- `chronic_conditions` (text, nullable)
- `surgery_history` (boolean, nullable)
- `family_history` (text, nullable)
- `completed` (boolean)
- `created_at` (datetime)
- `updated_at` (datetime)

### `phone_sessions`
- `id` (int, PK)
- `session_id` (string, unique)
- `caller_phone` (string, nullable)
- `room_name` (string, nullable)
- `status` (string) — `active`, `completed`, `disconnected`
- `duration_seconds` (int)
- `started_at` (datetime)
- `ended_at` (datetime, nullable)

## Error Handling

All tools return `success: true/false` with an error message on failure:

```json
{
  "success": false,
  "error": "Slot 2026-05-08 at 14:00 with Dr. Sarah Johnson is already booked"
}
```

Common errors:
- **Slot already booked**: Another patient booked that time
- **Patient not found**: Phone number doesn't match any patient record
- **Invalid date/time**: Malformed YYYY-MM-DD or HH:MM
- **Database error**: Connection issue, transaction rollback, etc.

## Logging

All operations are logged to stdout at the configured level:

```
INFO - Appointment booked: APT-20260507120000
INFO - Intake saved for patient +1-555-0123
WARNING - Slot conflict detected: 2026-05-08 14:00
ERROR - Database error: connection pool exhausted
```

## Testing

Run unit tests:

```bash
uv run pytest tests/test_mcp_server.py -v
```

Tests cover:
- Tool response structures
- Slot generation logic
- Conflict detection
- Provider list

## Deployment

### Local Development
1. Start the MCP server: `python -m docseek_voice_agent.mcp_server`
2. Configure Claude Code to connect to it via `~/.claude/settings.json`

### Production (Docker Compose)
```yaml
version: "3.9"
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: docseek
      POSTGRES_USER: docseek
      POSTGRES_PASSWORD: ${DB_PASSWORD}

  mcp-server:
    build: .
    environment:
      DATABASE_URL: postgresql://docseek:${DB_PASSWORD}@postgres:5432/docseek
      LOG_LEVEL: info
    depends_on:
      - postgres

  voice-agent:
    build: .
    environment:
      MCP_SERVERS: docseek-appointments=http://mcp-server:8000
    depends_on:
      - mcp-server
```

### LiveKit Cloud
Deploy as a background service alongside the voice agent. The agent will automatically discover and use it.

## Roadmap

- [ ] **Google Calendar integration**: Sync available slots with real clinic calendar
- [ ] **Insurance verification**: Real-time insurance eligibility checks
- [ ] **SMS/Email notifications**: Send appointment confirmations
- [ ] **Waitlist management**: Handle cancellations with automatic patient notification
- [ ] **Analytics**: Track no-shows, cancellations, booking patterns
- [ ] **Multi-clinic support**: Handle multiple clinic locations with different hours/providers

## Troubleshooting

### MCP Server won't start
```bash
# Check if port is in use
lsof -i :8000

# Try with debug logging
LOG_LEVEL=debug python -m docseek_voice_agent.mcp_server
```

### Database connection fails
```bash
# Verify DATABASE_URL
echo $DATABASE_URL

# Test connection
python -c "from docseek_voice_agent.database import engine; engine.connect()"
```

### Voice agent doesn't see the server
Verify the MCP server is configured in `~/.claude/settings.json`:
```json
{
  "mcpServers": {
    "docseek-appointments": {
      "command": "python",
      "args": ["-m", "docseek_voice_agent.mcp_server"]
    }
  }
}
```

---

For more details, see [ARCHITECTURE.md](./ARCHITECTURE.md).
