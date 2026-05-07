# Clinic Setup Guide — DocSeek Voice Agent

Complete guide to configure the voice agent for your specific medical clinic.

## Overview

The agent can be configured at **two levels**:

1. **Clinic Level** — Configure for an entire clinic (all doctors, hours, address, etc.)
2. **Doctor Level** — Within a clinic, focus the agent on a specific doctor

```
┌─────────────────────────────────┐
│   CLINIC: Sterling Family Med   │  ← Load with CLINIC_ID
├─────────────────────────────────┤
│ ├─ Dr. Sarah Johnson            │
│ ├─ Dr. Michael Chen             │
│ └─ NP Emily Rodriguez           │  ← Focus on one with DOCTOR_ID
└─────────────────────────────────┘
```

## Quick Start (Sterling Family Medicine)

The agent comes pre-configured for **Sterling Family Medicine** with 3 doctors.

```bash
# In .env.local:
CLINIC_ID=sterling-family-medicine
DOCTOR_ID=dr-sarah-johnson

# That's it! Start the agent:
python src/agent.py start
```

The agent will:
- Greet patients on behalf of Sterling Family Medicine
- Focus appointments on Dr. Sarah Johnson (but handle other doctors too)
- Use clinic hours: M-F 8am-5pm, W 8am-12pm, Sat 9am-12pm
- Share address, phone, insurance accepted, etc.

## Configuration Methods

### Method 1: Built-in Clinic (No Setup)

Uses pre-configured clinic profile.

```bash
# .env.local
CLINIC_ID=sterling-family-medicine
DOCTOR_ID=dr-sarah-johnson
```

**Available clinics:**
- `sterling-family-medicine` (3 doctors: Johnson, Chen, Rodriguez)

### Method 2: Custom Clinics (JSON File)

Define your clinic in `clinics.json`:

```json
{
  "your-clinic-id": {
    "name": "Your Clinic Name",
    "address": "123 Main St, City, ST 12345",
    "phone": "+1-555-0123",
    "timezone": "America/Chicago",
    "email": "info@yourclinic.com",
    "website": "www.yourclinic.com",
    "doctors": [
      {
        "id": "dr-name",
        "name": "Dr. Name",
        "title": "MD",
        "speciality": "Specialty",
        "bio": "Professional bio...",
        "email": "doctor@clinic.com",
        "phone": "555-0100",
        "accepts_new_patients": true
      }
    ],
    "office_hours": {
      "monday": "8:00 AM - 5:00 PM",
      "tuesday": "8:00 AM - 5:00 PM",
      ...
    }
  }
}
```

Then configure:

```bash
# .env.local
CLINIC_ID=your-clinic-id
DOCTOR_ID=dr-name
```

And load in code:

```python
from docseek_voice_agent.clinic_config import load_custom_clinics

load_custom_clinics("clinics.json")
```

### Method 3: Manual Fallback (No Profile)

If `CLINIC_ID` not set, uses manual settings:

```bash
# .env.local
CLINIC_NAME=Your Clinic
CLINIC_TIMEZONE=America/New_York
CLINIC_PHONE=+1-555-0123
```

⚠️ **Less flexible** — no doctor profiles, hours, address. Use Method 1 or 2 instead.

## Clinic Profile Schema

```python
@dataclass
class ClinicProfile:
    id: str                              # Unique identifier
    name: str                            # Clinic name
    address: str                         # Physical address
    phone: str                           # Main phone number
    timezone: str                        # Clinic timezone
    email: Optional[str]                 # Contact email
    website: Optional[str]               # Website URL
    doctors: List[DoctorProfile]         # All doctors/providers
    office_hours: Dict[str, str]         # Day -> hours
    accepts_insurance: List[str]         # Insurance plans accepted
    tagline: Optional[str]               # Marketing tagline
    patient_notice: Optional[str]        # Important patient info

    # Methods
    get_doctor_by_name(doctor_name)      # Find doctor by name
    get_doctor_by_id(doctor_id)          # Find doctor by ID
    list_accepting_patients()            # Get doctors accepting new patients
    to_dict()                            # Convert to dictionary
```

## Doctor Profile Schema (Within Clinic)

```python
@dataclass
class DoctorProfile:
    id: str                              # Unique ID (e.g., "dr-name")
    name: str                            # Full name
    title: str                           # Medical title (MD, DO, NP-C, PA-C)
    speciality: str                      # Medical speciality
    bio: str                             # Professional biography
    email: Optional[str]                 # Email
    phone: Optional[str]                 # Phone
    office_hours: Optional[dict]         # Override clinic hours
    default_appointment_duration: int    # Minutes (default 30)
    availability_buffer: int             # Minutes between appointments
    accepts_new_patients: bool           # Accepting new patients?
```

## Usage Examples

### Single-Doctor Clinic

```json
{
  "dr-smith-practice": {
    "name": "Dr. Smith's Practice",
    "address": "100 Medical Ave, Boston, MA",
    "phone": "+1-617-555-0100",
    "timezone": "America/New_York",
    "doctors": [
      {
        "id": "dr-john-smith",
        "name": "Dr. John Smith",
        "title": "MD",
        "speciality": "Orthopedic Surgery",
        "bio": "Dr. Smith specializes in sports medicine...",
        "accepts_new_patients": true
      }
    ]
  }
}
```

Config:
```bash
CLINIC_ID=dr-smith-practice
# DOCTOR_ID is optional (only one doctor anyway)
```

### Multi-Specialty Clinic

```json
{
  "city-medical-center": {
    "name": "City Medical Center",
    "address": "500 Health St, NY, NY 10001",
    "phone": "+1-212-555-0500",
    "timezone": "America/New_York",
    "doctors": [
      {
        "id": "dr-cardio",
        "name": "Dr. Cardio",
        "speciality": "Cardiology",
        ...
      },
      {
        "id": "dr-ortho",
        "name": "Dr. Ortho",
        "speciality": "Orthopedics",
        ...
      },
      {
        "id": "dr-neuro",
        "name": "Dr. Neuro",
        "speciality": "Neurology",
        ...
      }
    ]
  }
}
```

Config:
```bash
CLINIC_ID=city-medical-center
DOCTOR_ID=dr-cardio   # Agent focuses on cardiology

# Or run multiple agents, one per doctor:
# DOCTOR_ID=dr-ortho
# DOCTOR_ID=dr-neuro
```

### Clinic with Rotating Hours

```json
{
  "urgent-care": {
    "office_hours": {
      "monday": "9:00 AM - 9:00 PM",
      "tuesday": "9:00 AM - 9:00 PM",
      "wednesday": "9:00 AM - 9:00 PM",
      "thursday": "9:00 AM - 9:00 PM",
      "friday": "9:00 AM - 9:00 PM",
      "saturday": "8:00 AM - 6:00 PM",
      "sunday": "10:00 AM - 4:00 PM"
    },
    "doctors": [
      {
        "id": "dr-day",
        "name": "Dr. Day Shift",
        "office_hours": {
          "monday": "8:00 AM - 4:00 PM",
          "tuesday": "8:00 AM - 4:00 PM",
          ...
        }
      },
      {
        "id": "dr-night",
        "name": "Dr. Night Shift",
        "office_hours": {
          "monday": "4:00 PM - 12:00 AM",
          ...
        }
      }
    ]
  }
}
```

## Agent Behavior by Configuration

### With Clinic + Doctor

```
Agent prompt: "You are the front desk for [Clinic Name], 
primarily scheduling appointments with [Doctor Name]."

Patient: "I'd like an appointment"
Agent: "I can book you with [Doctor Name], a [Speciality] specialist.
        They're accepting new patients and have availability..."
```

### With Clinic Only (No Doctor)

```
Agent prompt: "You are the front desk for [Clinic Name].
             I can help you with any of our providers."

Patient: "Who would you recommend?"
Agent: "We have [Dr A], [Dr B], and [Dr C].
        Which provider would you prefer?"
```

### Manual Settings Only

```
Agent prompt: "You are the front desk for [Clinic Name]."

Patient: "Who are your doctors?"
Agent: "I'd be happy to help. Let me get you the information..."
```

## Setup Checklist

- [ ] Decide: Single doctor or multi-doctor clinic?
- [ ] Choose configuration method:
  - [ ] Built-in clinic (if Sterling Family Medicine)
  - [ ] Custom JSON file
  - [ ] Manual .env.local
- [ ] If using custom clinic:
  - [ ] Create `clinics.json` with all doctors
  - [ ] Verify JSON is valid: `python -m json.tool clinics.json`
  - [ ] Add load call in code: `load_custom_clinics("clinics.json")`
- [ ] Set in `.env.local`:
  - [ ] `CLINIC_ID=your-clinic-id`
  - [ ] `DOCTOR_ID=doctor-id` (optional)
- [ ] Test: `python src/agent.py console`
  - [ ] Agent mentions clinic name ✓
  - [ ] Agent mentions doctor (if configured) ✓
  - [ ] Can list available doctors ✓

## Advanced: Custom Doctor Logic

To add special handling (rotating doctors, on-call schedules, etc.):

```python
from docseek_voice_agent.clinic_config import ClinicProfile, DoctorProfile

class CustomClinicProfile(ClinicProfile):
    def get_available_doctors(self, date_str: str) -> List[DoctorProfile]:
        """Override to add custom scheduling logic."""
        # Check if doctor is on-call that day
        # Check PTO/vacation
        # Check rotating schedule
        # etc.
        return [d for d in self.doctors if d.is_available_on(date_str)]
```

## Troubleshooting

### "Clinic profile not found"

```bash
# Check available clinics
python -c "from docseek_voice_agent.clinic_config import list_clinics; print(list_clinics())"

# Verify CLINIC_ID spelling (case-insensitive but must exist)
echo $CLINIC_ID
```

### Custom clinic not loading

```bash
# Verify JSON is valid
python -m json.tool clinics.json

# Check load call happens before agent starts
grep "load_custom_clinics" src/agent.py
```

### Doctor not found in clinic

```bash
# List doctors in clinic
python -c "
from docseek_voice_agent.clinic_config import get_clinic_profile
clinic = get_clinic_profile('sterling-family-medicine')
print([d.id for d in clinic.doctors])
"
```

### Agent doesn't mention clinic/doctor

Check the agent system prompt was generated correctly:

```python
from docseek_voice_agent.clinic_logic import MedicalAgentPrompt
prompt = MedicalAgentPrompt.system_prompt("Sterling Family Medicine", "Dr. Sarah Johnson")
print(prompt)
```

## See Also

- [DOCTOR_CONFIG.md](./DOCTOR_CONFIG.md) — Doctor-level configuration
- [MCP_SERVER.md](./MCP_SERVER.md) — Appointment booking
- [ARCHITECTURE.md](./ARCHITECTURE.md) — System design
- [README.md](./README.md) — Full documentation
