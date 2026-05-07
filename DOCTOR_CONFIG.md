# Doctor Configuration — DocSeek Voice Agent

Configure the voice agent to specialize in a specific doctor's schedule and practice.

## Quick Start

### Option 1: Built-in Profiles (No Setup Needed)

The agent comes with three built-in doctor profiles:

```bash
# Dr. Sarah Johnson — Internal Medicine
DOCTOR_ID=dr-sarah-johnson

# Dr. Michael Chen — Cardiology
DOCTOR_ID=dr-michael-chen

# Nurse Practitioner Emily Rodriguez — Family Medicine
DOCTOR_ID=np-emily-rodriguez
```

Set `DOCTOR_ID` in `.env.local`:

```bash
cd ~/Projects/docseek-voice-agent
echo "DOCTOR_ID=dr-sarah-johnson" >> .env.local
python -m docseek_voice_agent.mcp_server
```

The agent will:
- Greet patients on behalf of that doctor
- Prioritize their schedule when booking appointments
- Share their bio and speciality when relevant

### Option 2: Custom Doctors (JSON Config)

Add your own doctors in `doctors.json`:

```json
{
  "dr-john-smith": {
    "name": "Dr. John Smith",
    "title": "MD",
    "speciality": "Orthopedic Surgery",
    "bio": "Dr. Smith has 20 years of experience in sports medicine and joint replacement.",
    "email": "jsmith@hospital.com",
    "phone": "555-2001",
    "office_hours": {
      "monday": "9:00 AM - 5:00 PM",
      "tuesday": "9:00 AM - 5:00 PM",
      "wednesday": "CLOSED",
      "thursday": "9:00 AM - 5:00 PM",
      "friday": "9:00 AM - 2:00 PM"
    },
    "default_appointment_duration": 45,
    "availability_buffer": 20,
    "accepts_new_patients": true
  }
}
```

Then load it in code:

```python
from docseek_voice_agent.doctor_config import load_custom_profiles

load_custom_profiles("doctors.json")
```

## Configuration Reference

### Built-in Doctors

| ID | Name | Speciality | New Patients | Hours |
|---|---|---|---|---|
| `dr-sarah-johnson` | Dr. Sarah Johnson, MD | Internal Medicine | ✅ Yes | M-F 8am-5pm (W 8am-12pm) |
| `dr-michael-chen` | Dr. Michael Chen, MD | Cardiology | ❌ No | M,T,Th,F 9am-5pm (F 9am-2pm) |
| `np-emily-rodriguez` | NP Emily Rodriguez, NP-C | Family Medicine | ✅ Yes | M-F 8am-6pm (F 8am-4pm) |

### Doctor Profile Schema

```python
@dataclass
class DoctorProfile:
    id: str                          # Unique identifier (e.g., "dr-sarah-johnson")
    name: str                        # Full name with title (e.g., "Dr. Sarah Johnson")
    title: str                       # Medical title (MD, DO, NP-C, PA-C, etc.)
    speciality: str                  # Medical speciality
    bio: str                         # Professional biography
    email: Optional[str]             # Email address
    phone: Optional[str]             # Phone number
    office_hours: Optional[dict]     # Day -> hours mapping
    default_appointment_duration: int = 30  # Minutes
    availability_buffer: int = 15    # Minutes between appointments
    accepts_new_patients: bool       # Accepting new patients?
```

## Using Doctor Profiles

### In Environment

```bash
# Use built-in profile
DOCTOR_ID=dr-sarah-johnson

# Or with environment variable
export DOCTOR_NAME="Dr. Sarah Johnson"
python src/agent.py start
```

### In Code

```python
from docseek_voice_agent.doctor_config import get_doctor_profile

# Get built-in profile
doctor = get_doctor_profile("dr-sarah-johnson")

# List all available doctors
from docseek_voice_agent.doctor_config import list_doctors
doctors = list_doctors()  # ["dr-sarah-johnson", "dr-michael-chen", ...]

# Load from environment
from docseek_voice_agent.doctor_config import get_doctor_profile_from_env
doctor = get_doctor_profile_from_env()  # Uses DOCTOR_ID or DOCTOR_NAME env var
```

### Updating Agent Prompt

The agent's system prompt automatically includes doctor information:

```python
from docseek_voice_agent.clinic_logic import MedicalAgentPrompt
from docseek_voice_agent.config import settings

# Generate prompt for specific doctor
prompt = MedicalAgentPrompt.system_prompt(
    clinic_name=settings.clinic_name,
    doctor_name="Dr. Sarah Johnson"
)

# Also include doctor bio
doctor_info = MedicalAgentPrompt.doctor_info_prompt("Dr. Sarah Johnson")
```

## Customization Examples

### Add a New Doctor

Create `doctors.json`:

```json
{
  "dr-alice-patel": {
    "name": "Dr. Alice Patel",
    "title": "MD",
    "speciality": "Pediatrics",
    "bio": "Dr. Patel is a board-certified pediatrician with special interest in developmental pediatrics.",
    "email": "apatel@clinic.com",
    "phone": "555-3001",
    "office_hours": {
      "monday": "8:30 AM - 4:30 PM",
      "tuesday": "8:30 AM - 4:30 PM",
      "wednesday": "CLOSED",
      "thursday": "8:30 AM - 4:30 PM",
      "friday": "8:30 AM - 12:30 PM"
    },
    "default_appointment_duration": 30,
    "accepts_new_patients": true
  }
}
```

Then in your code:

```python
from docseek_voice_agent.doctor_config import load_custom_profiles

load_custom_profiles("doctors.json")

# Now use it
doctor = get_doctor_profile("dr-alice-patel")
```

### Change Doctor at Runtime

```python
import os
from docseek_voice_agent.doctor_config import get_doctor_profile_from_env

# Set environment variable
os.environ["DOCTOR_ID"] = "dr-michael-chen"

# Get the profile
doctor = get_doctor_profile_from_env()
print(f"Now scheduling for {doctor.name}")
```

### Multi-Doctor Setup

If your clinic has multiple doctors, you can run separate agent instances:

```bash
# Terminal 1: Dr. Johnson's agent
DOCTOR_ID=dr-sarah-johnson python src/agent.py start

# Terminal 2: Dr. Chen's agent
DOCTOR_ID=dr-michael-chen python src/agent.py start

# Terminal 3: NP Rodriguez's agent
DOCTOR_ID=np-emily-rodriguez python src/agent.py start
```

Each agent focuses on their respective doctor's schedule.

## Integration with Appointment System

The doctor profile integrates with the MCP appointment server:

```
Voice Agent + Doctor Profile
         ↓
LLM sees: "You are scheduling for Dr. Sarah Johnson, Internal Medicine"
         ↓
Patient: "I'd like to see Dr. Johnson"
         ↓
Agent calls: get_available_slots(provider="Dr. Sarah Johnson")
         ↓
MCP Server queries database for Dr. Johnson's appointments
         ↓
Returns available 30-min slots (duration from profile)
```

## Handling Multiple Doctors

When a patient requests a different doctor, the agent can switch contexts:

```
Patient: "Actually, can I see Dr. Chen instead?"

Agent checks: Is Dr. Chen accepting new patients?
  → Yes: Switch context and check their availability
  → No: "Dr. Chen is not accepting new patients at this time.
          I can book you with Dr. Johnson or NP Rodriguez instead."
```

## Advanced: Custom Office Hours Logic

For complex scheduling (rotating hours, covering doctors, etc.), extend the `DoctorProfile`:

```python
@dataclass
class DoctorProfile:
    # ... existing fields ...
    
    # Custom methods
    def is_available_on(self, date_str: str) -> bool:
        """Check if doctor is available on a specific date."""
        # Custom logic: check holidays, PTO, rotating schedule, etc.
        pass
    
    def get_appointment_slots(self, date_str: str) -> List[str]:
        """Get available time slots for a specific date."""
        # Use office_hours + availability_buffer to generate slots
        pass
```

## Troubleshooting

### Doctor not found

```python
from docseek_voice_agent.doctor_config import list_doctors, get_doctor_profile

# Check available doctors
print(list_doctors())  # ['dr-sarah-johnson', 'dr-michael-chen', 'np-emily-rodriguez']

# Verify ID matches
doctor = get_doctor_profile("dr-SARAH-johnson")  # Case-insensitive
```

### Environment variable not loading

```bash
# Verify it's set
echo $DOCTOR_ID

# Set explicitly in .env.local
echo "DOCTOR_ID=dr-sarah-johnson" >> .env.local

# Or in code
import os
os.environ["DOCTOR_ID"] = "dr-sarah-johnson"
```

### Custom doctors not loading

```python
# Verify JSON is valid
import json
with open("doctors.json") as f:
    json.load(f)  # Will raise if invalid

# Load and verify
from docseek_voice_agent.doctor_config import load_custom_profiles
load_custom_profiles("doctors.json")
```

## Best Practices

1. **Use built-in profiles for testing** — They're pre-configured and require no setup
2. **Load custom profiles early** — Call `load_custom_profiles()` before starting the agent
3. **Set `DOCTOR_ID` in `.env.local`** — Keeps configuration per-environment
4. **Include complete bios** — The agent shares these with patients; make them professional
5. **Keep office hours updated** — Accuracy matters for scheduling
6. **Set `accepts_new_patients`** — Prevents booking new patients with doctors who aren't accepting them

## See Also

- [MCP_SERVER.md](./MCP_SERVER.md) — Appointment scheduling system
- [ARCHITECTURE.md](./ARCHITECTURE.md) — System design
- [README.md](./README.md) — Full documentation
