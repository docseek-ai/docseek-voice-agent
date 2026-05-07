# DocSeek Medical Front Desk Voice Agent

A realtime AI voice agent for medical offices that handles appointment scheduling, patient intake, and front desk inquiries.

## Features

- **Appointment Scheduling**: Books appointments with available providers
- **Patient Intake**: Collects health history and insurance information via voice
- **Call Routing**: Handles common inquiries and routes to appropriate staff
- **Natural Conversation**: Uses advanced speech recognition and language models for human-like interactions
- **Multi-Provider Support**: Works with multiple providers and clinic locations
- **HIPAA-Aware**: Designed with privacy and security considerations for medical data

## Architecture

The agent uses a **STT-LLM-TTS pipeline**:

1. **Speech-to-Text (STT)**: Converts patient audio to text using Deepgram
2. **Large Language Model (LLM)**: Processes text and generates intelligent responses using OpenAI GPT-4o-mini
3. **Text-to-Speech (TTS)**: Converts responses back to natural-sounding speech using OpenAI

Built on the [LiveKit Agents](https://github.com/livekit/agents) framework for realtime, low-latency voice interaction.

## Prerequisites

- Python 3.11+
- LiveKit Cloud account or self-hosted LiveKit server
- OpenAI API key
- Deepgram API key (for advanced STT)
- PostgreSQL or SQLite for appointment/patient records

## Quick Start

### 1. Clone & Setup

```bash
cd ~/Projects/docseek-voice-agent
uv sync
cp .env.example .env.local
```

### 2. Configure Environment

Edit `.env.local` with your credentials:

```bash
# LiveKit
LIVEKIT_URL=wss://your-livekit-instance.com
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# LLM
OPENAI_API_KEY=sk-...

# STT
DEEPGRAM_API_KEY=your-deepgram-key

# Clinic Info
CLINIC_NAME="Your Medical Practice"
CLINIC_PHONE="+1-555-0123"
```

### 3. Download Required Models

```bash
uv run python src/agent.py download-files
```

### 4. Run in Console Mode

```bash
uv run python src/agent.py console
```

This opens an interactive terminal where you can type messages and see the agent's responses.

### 5. Development Mode

```bash
uv run python src/agent.py dev
```

Auto-reloads on code changes. Great for iteration.

### 6. Production Mode

```bash
uv run python src/agent.py start
```

Runs the agent as a service ready to accept incoming calls.

## Project Structure

```
docseek-voice-agent/
├── src/
│   ├── agent.py                  # Main agent entry point
│   └── docseek_voice_agent/
│       ├── __init__.py
│       ├── config.py             # Configuration management
│       ├── clinic_logic.py        # Medical-specific logic
│       ├── database.py           # SQLAlchemy models
│       └── api.py                # REST API endpoints (optional)
├── tests/                        # Unit and integration tests
├── pyproject.toml               # Dependencies and build config
├── .env.example                 # Example environment variables
└── README.md
```

## Key Components

### Agent (`src/agent.py`)

The main voice agent that:
- Greets patients warmly
- Collects appointment preferences
- Confirms patient information
- Schedules appointments
- Answers common office questions

### Clinic Logic (`clinic_logic.py`)

Medical-specific features:
- **MedicalAgentPrompt**: System prompts tailored for clinic receptionists
- **AppointmentHandler**: Manages appointment availability and booking
- **PatientIntakeForm**: Structured health history collection

### Database Models (`database.py`)

SQLAlchemy ORM models for:
- **Patient**: Patient records and contact info
- **Appointment**: Scheduled appointments with confirmation details
- **PatientIntakeRecord**: Health history responses
- **PhoneSession**: Call tracking and analytics

## Configuration

All settings are managed via environment variables in `.env.local`:

| Variable | Default | Description |
|----------|---------|-------------|
| LIVEKIT_URL | ws://localhost:7880 | LiveKit server URL |
| LIVEKIT_API_KEY | - | LiveKit API credentials |
| OPENAI_API_KEY | - | OpenAI API key for LLM and TTS |
| DEEPGRAM_API_KEY | - | Deepgram API key for STT |
| DATABASE_URL | sqlite:///docseek_voice.db | Database connection string |
| CLINIC_NAME | DocSeek Medical | Name of clinic for greeting |
| CLINIC_PHONE | +1-555-0123 | Clinic's phone number |
| CLINIC_TIMEZONE | America/Chicago | Clinic timezone for scheduling |

## Testing

Run tests with:

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=src

# Specific test file
uv run pytest tests/test_appointment_handler.py -v
```

## Deployment

### Docker

```bash
docker build -t docseek-voice-agent .
docker run -e LIVEKIT_API_KEY=... -e OPENAI_API_KEY=... docseek-voice-agent
```

### LiveKit Cloud

Deploy directly to LiveKit Cloud:

```bash
lk agent create --template ./
lk agent logs <agent-name>
```

## Common Use Cases

### Scheduling an Appointment

```
Patient: "I'd like to schedule an appointment"
Agent: "Of course! What's the reason for your visit?"
Patient: "I need a checkup"
Agent: "Great. What date and time work best for you?"
Patient: "Next Tuesday at 2 PM"
Agent: "Perfect! I have Dr. Johnson available Tuesday at 2 PM. 
        Let me confirm your information..."
```

### Patient Intake

```
Agent: "Before your appointment, I'll need to collect some health information.
        Do you have any known allergies?"
Patient: "Penicillin"
Agent: "Noted. Are you currently taking any medications?"
...
```

## Roadmap

- [ ] Integration with calendar systems (Google Calendar, Outlook)
- [ ] SMS confirmations for appointments
- [ ] Multi-language support
- [ ] Voice biometric authentication
- [ ] Insurance verification integration
- [ ] EHR/EMR system connectors
- [ ] Advanced analytics dashboard

## Troubleshooting

### Agent won't start

Check that LiveKit is running:
```bash
curl -i http://localhost:7880/health
```

### STT/TTS Errors

Verify API keys are correct in `.env.local`:
```bash
# Test OpenAI
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Test Deepgram
curl https://api.deepgram.com/v1/models \
  -H "Authorization: Token $DEEPGRAM_API_KEY"
```

### Database Connection Issues

For PostgreSQL:
```bash
psql postgresql://user:password@localhost:5432/docseek_voice
```

For SQLite (default):
```bash
sqlite3 docseek_voice.db
```

## Development Notes

- **Code Style**: Black formatter, Ruff linter. Run `black src/` and `ruff check src/`
- **Type Checking**: MyPy enabled. Run `mypy src/`
- **Async/Await**: The agent is fully async using Python's asyncio
- **Logging**: Structured logging to help with debugging

## Resources

- [LiveKit Agents Documentation](https://docs.livekit.io/agents/)
- [LiveKit Python Starter](https://github.com/livekit-examples/agent-starter-python)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Deepgram STT Documentation](https://developers.deepgram.com/reference)

## License

MIT

## Support

For issues and questions:
1. Check the [LiveKit documentation](https://docs.livekit.io/)
2. Review existing [GitHub issues](https://github.com/livekit/agents/issues)
3. Open a new issue with details about your problem
