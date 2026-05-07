# DocSeek Voice Agent — Quick Start Guide

Get the medical front desk voice agent running in 5 minutes.

## 1. Install Dependencies

```bash
cd ~/Projects/docseek-voice-agent
uv sync
```

(If you don't have `uv`, install it: `curl -LsSf https://astral.sh/uv/install.sh | sh`)

## 2. Set Up Environment

```bash
cp .env.example .env.local
```

Edit `.env.local` with your API keys:

```bash
# Required
LIVEKIT_URL=wss://your-livekit-url.com  # or ws://localhost:7880 for local dev
LIVEKIT_API_KEY=your-key
LIVEKIT_API_SECRET=your-secret
OPENAI_API_KEY=sk-...
DEEPGRAM_API_KEY=...

# Optional but recommended
CLINIC_NAME="Your Medical Practice"
CLINIC_PHONE="+1-555-0123"
```

## 3. Download Models

```bash
uv run python src/agent.py download-files
```

This downloads Silero VAD and other required models (~500MB). Only needs to happen once.

## 4. Test in Console Mode

```bash
uv run python src/agent.py console
```

You'll see a chat interface. Type a message and watch the agent respond:

```
Enter message: "Hi, I'd like to schedule an appointment"

Agent: "Hello! Thank you for calling DocSeek Medical. 
How can I help you today? Are you looking to schedule an appointment 
or do you have a question?"
```

Type `exit` to quit.

## 5. Run in Dev Mode

```bash
uv run python src/agent.py dev
```

Watches for code changes and auto-reloads. Perfect for iteration. Connects to a local LiveKit instance.

## 6. Connect LiveKit (Optional)

If you want to test with actual voice, set up LiveKit:

### Option A: Local LiveKit (Recommended for Dev)

```bash
docker run --rm -d \
  -p 7880:7880 \
  -p 7881:7881 \
  -p 7882:7882/udp \
  --name livekit \
  livekit/livekit-server:latest \
  --dev
```

Then update `.env.local`:
```
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
```

### Option B: LiveKit Cloud

1. Create account at [livekit.io](https://livekit.io)
2. Create a project and grab credentials
3. Update `.env.local` with your URL and keys

## Key Files to Know

| File | Purpose |
|------|---------|
| `src/agent.py` | Main agent entry point—handles greeting, routing, scheduling |
| `src/docseek_voice_agent/clinic_logic.py` | Medical logic: appointments, intake forms, prompts |
| `src/docseek_voice_agent/config.py` | Configuration from environment variables |
| `src/docseek_voice_agent/database.py` | SQLAlchemy models (Patient, Appointment, etc.) |
| `tests/test_clinic_logic.py` | Unit tests for appointment handler and intake |
| `.env.local` | Your API keys and clinic settings (git-ignored) |

## Next Steps

1. **Customize the system prompt** — Edit `clinic_logic.py`, `MedicalAgentPrompt.system_prompt()`
2. **Add database persistence** — Uncomment the database code in `agent.py` and run migrations
3. **Deploy to LiveKit Cloud** — Use `lk agent create` (see README.md)
4. **Run tests** — `uv run pytest tests/`

## Troubleshooting

### "ModuleNotFoundError: No module named 'livekit'"

Run `uv sync` again. The dependency didn't install correctly.

### "Connection refused" when starting agent

Make sure LiveKit is running:
- If local: `docker ps | grep livekit` should show a running container
- If cloud: Check credentials in `.env.local`

### Agent won't respond

Check the logs. The agent should print to stdout:
```
INFO - Starting medical front desk agent in room: test-room
```

If you see errors, usually it's a missing API key. Verify in `.env.local`.

### Tests fail

Ensure you have the test dependencies:
```bash
uv sync  # This should pull pytest, pytest-asyncio, etc.
uv run pytest tests/ -v
```

## Live Voice Testing

Once you have LiveKit running, test with real voice:

1. Open a second terminal and run the agent:
   ```bash
   uv run python src/agent.py start
   ```

2. Use the [LiveKit CLI](https://docs.livekit.io/cli/) to create a test room:
   ```bash
   lk room create test-room
   ```

3. Connect with a sample app or the browser-based [LiveKit Console](https://cloud.livekit.io)

## Next: Function Calling

The agent currently uses natural language for appointments. To make it more reliable (e.g., guaranteed booking), add **function calling**:

1. Define tool functions in `clinic_logic.py`
2. Pass them to the LLM via the LiveKit Agents framework
3. The agent will call them when needed

This lets the agent trigger code (book an appointment, verify insurance) automatically instead of just talking about it.

---

Questions? Check the [LiveKit Agents docs](https://docs.livekit.io/agents/) or open an issue.
