"""Clinic-specific configuration profiles for the voice agent.

This module allows complete configuration of the agent for a specific medical clinic,
including all doctors/providers, hours, address, and contact information.

Usage:
    from docseek_voice_agent.clinic_config import get_clinic_profile

    clinic = get_clinic_profile("sterling-family-medicine")
    # clinic.name, clinic.phone, clinic.doctors, clinic.hours, etc.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
import json
from pathlib import Path
import logging

from docseek_voice_agent.doctor_config import DoctorProfile

logger = logging.getLogger(__name__)


@dataclass
class ClinicProfile:
    """Configuration profile for a specific medical clinic."""

    id: str
    name: str
    address: str
    phone: str
    timezone: str
    email: Optional[str] = None
    website: Optional[str] = None
    doctors: List[DoctorProfile] = field(default_factory=list)

    # Clinic hours (applies to all doctors unless overridden)
    office_hours: Dict[str, str] = field(default_factory=lambda: {
        "monday": "8:00 AM - 5:00 PM",
        "tuesday": "8:00 AM - 5:00 PM",
        "wednesday": "8:00 AM - 5:00 PM",
        "thursday": "8:00 AM - 5:00 PM",
        "friday": "8:00 AM - 5:00 PM",
        "saturday": "CLOSED",
        "sunday": "CLOSED",
    })

    holidays_closed: List[str] = field(default_factory=list)  # ["2026-12-25", "2026-01-01"]

    # Insurance info
    accepts_insurance: List[str] = field(default_factory=list)

    # Clinic info for agent
    tagline: Optional[str] = None
    patient_notice: Optional[str] = None

    def get_doctor_by_name(self, doctor_name: str) -> Optional[DoctorProfile]:
        """Get a doctor by name."""
        for doctor in self.doctors:
            if doctor.name.lower() == doctor_name.lower():
                return doctor
        return None

    def get_doctor_by_id(self, doctor_id: str) -> Optional[DoctorProfile]:
        """Get a doctor by ID."""
        for doctor in self.doctors:
            if doctor.id.lower() == doctor_id.lower():
                return doctor
        return None

    def list_accepting_patients(self) -> List[DoctorProfile]:
        """Get list of doctors accepting new patients."""
        return [d for d in self.doctors if d.accepts_new_patients]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "phone": self.phone,
            "timezone": self.timezone,
            "email": self.email,
            "website": self.website,
            "doctors": [d.to_dict() for d in self.doctors],
            "office_hours": self.office_hours,
            "accepts_insurance": self.accepts_insurance,
            "tagline": self.tagline,
            "patient_notice": self.patient_notice,
        }


# Built-in clinic profiles
CLINIC_PROFILES = {
    "sterling-family-medicine": ClinicProfile(
        id="sterling-family-medicine",
        name="Sterling Family Medicine",
        address="123 Main St, Springfield, IL 62701",
        phone="+1-217-555-0100",
        timezone="America/Chicago",
        email="info@sterlingfamilymedicine.com",
        website="www.sterlingfamilymedicine.com",
        tagline="Compassionate primary care for your whole family",
        accepts_insurance=["Aetna", "Blue Cross Blue Shield", "Cigna", "Medicare", "Medicaid"],
        office_hours={
            "monday": "8:00 AM - 5:00 PM",
            "tuesday": "8:00 AM - 5:00 PM",
            "wednesday": "8:00 AM - 12:00 PM",
            "thursday": "8:00 AM - 5:00 PM",
            "friday": "8:00 AM - 5:00 PM",
            "saturday": "9:00 AM - 12:00 PM",
            "sunday": "CLOSED",
        },
        doctors=[
            DoctorProfile(
                id="dr-sarah-johnson",
                name="Dr. Sarah Johnson",
                title="MD",
                speciality="Internal Medicine",
                bio="Dr. Johnson is a board-certified internist with 15+ years of experience in primary care and chronic disease management.",
                email="sjohnson@sterlingfamilymedicine.com",
                phone="555-0101",
                accepts_new_patients=True,
            ),
            DoctorProfile(
                id="dr-michael-chen",
                name="Dr. Michael Chen",
                title="MD",
                speciality="Cardiology",
                bio="Dr. Chen specializes in preventive cardiology and is an expert in managing hypertension and heart disease.",
                email="mchen@sterlingfamilymedicine.com",
                phone="555-0102",
                accepts_new_patients=False,
            ),
            DoctorProfile(
                id="np-emily-rodriguez",
                name="Nurse Practitioner Emily Rodriguez",
                title="NP-C",
                speciality="Family Medicine",
                bio="NP Rodriguez provides comprehensive family medicine care including preventive health, minor acute illness, and chronic disease management.",
                email="erodriguez@sterlingfamilymedicine.com",
                phone="555-0103",
                accepts_new_patients=True,
            ),
        ],
    ),
}


def get_clinic_profile(clinic_id: str) -> Optional[ClinicProfile]:
    """Get a clinic profile by ID.

    Args:
        clinic_id: Clinic profile ID (e.g., 'sterling-family-medicine')

    Returns:
        ClinicProfile if found, None otherwise
    """
    profile = CLINIC_PROFILES.get(clinic_id.lower())
    if not profile:
        logger.warning(f"Clinic profile not found: {clinic_id}")
    return profile


def list_clinics() -> List[str]:
    """List all available clinic profile IDs."""
    return list(CLINIC_PROFILES.keys())


def get_clinic_profile_from_env() -> Optional[ClinicProfile]:
    """Load clinic profile from environment variable.

    Reads CLINIC_ID environment variable.

    Returns:
        ClinicProfile if configured, None otherwise
    """
    import os

    clinic_id = os.getenv("CLINIC_ID")
    if not clinic_id:
        return None

    return get_clinic_profile(clinic_id)


def load_custom_clinics(config_path: str) -> None:
    """Load additional clinic profiles from a JSON file.

    File format:
        {
            "clinic-id": {
                "name": "Clinic Name",
                "address": "123 Main St",
                "phone": "+1-555-0000",
                "timezone": "America/Chicago",
                "email": "info@clinic.com",
                "doctors": [
                    {
                        "id": "dr-name",
                        "name": "Dr. Name",
                        "title": "MD",
                        "speciality": "Specialty",
                        "bio": "Bio...",
                        ...
                    }
                ],
                ...
            }
        }

    Args:
        config_path: Path to JSON configuration file
    """
    try:
        path = Path(config_path)
        if not path.exists():
            logger.warning(f"Clinic config file not found: {config_path}")
            return

        with open(path) as f:
            configs = json.load(f)

        for clinic_id, config in configs.items():
            # Parse doctors
            doctors = []
            for doctor_config in config.get("doctors", []):
                doctor = DoctorProfile(
                    id=doctor_config["id"],
                    name=doctor_config["name"],
                    title=doctor_config["title"],
                    speciality=doctor_config["speciality"],
                    bio=doctor_config["bio"],
                    email=doctor_config.get("email"),
                    phone=doctor_config.get("phone"),
                    office_hours=doctor_config.get("office_hours"),
                    default_appointment_duration=doctor_config.get("default_appointment_duration", 30),
                    availability_buffer=doctor_config.get("availability_buffer", 15),
                    accepts_new_patients=doctor_config.get("accepts_new_patients", True),
                )
                doctors.append(doctor)

            # Create clinic profile
            clinic = ClinicProfile(
                id=clinic_id,
                name=config["name"],
                address=config["address"],
                phone=config["phone"],
                timezone=config["timezone"],
                email=config.get("email"),
                website=config.get("website"),
                doctors=doctors,
                office_hours=config.get("office_hours", {}),
                accepts_insurance=config.get("accepts_insurance", []),
                tagline=config.get("tagline"),
                patient_notice=config.get("patient_notice"),
            )
            CLINIC_PROFILES[clinic_id] = clinic
            logger.info(f"Loaded clinic profile: {clinic_id} with {len(doctors)} doctor(s)")

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse clinic config: {e}")
    except KeyError as e:
        logger.error(f"Missing required field in clinic config: {e}")
