"""Doctor-specific configuration profiles for the voice agent.

This module allows easy configuration of the agent for specific doctors,
including their specialties, bios, and availability patterns.

Usage:
    from docseek_voice_agent.doctor_config import get_doctor_profile

    doctor = get_doctor_profile("dr-sarah-johnson")
    # or load from environment
    doctor = get_doctor_profile_from_env()
"""

from dataclasses import dataclass
from typing import Optional, List
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class DoctorProfile:
    """Configuration profile for a specific doctor."""

    id: str
    name: str
    title: str
    speciality: str
    bio: str
    email: Optional[str] = None
    phone: Optional[str] = None
    office_hours: Optional[dict] = None  # day -> hours dict
    default_appointment_duration: int = 30  # minutes
    availability_buffer: int = 15  # minutes between appointments
    accepts_new_patients: bool = True

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "title": self.title,
            "speciality": self.speciality,
            "bio": self.bio,
            "email": self.email,
            "phone": self.phone,
            "office_hours": self.office_hours,
            "default_appointment_duration": self.default_appointment_duration,
            "availability_buffer": self.availability_buffer,
            "accepts_new_patients": self.accepts_new_patients,
        }


# Built-in doctor profiles
DOCTOR_PROFILES = {
    "dr-sarah-johnson": DoctorProfile(
        id="dr-sarah-johnson",
        name="Dr. Sarah Johnson",
        title="MD",
        speciality="Internal Medicine",
        bio="Dr. Johnson is a board-certified internist with 15+ years of experience in primary care and chronic disease management.",
        email="sjohnson@docseek.com",
        phone="555-0101",
        office_hours={
            "monday": "8:00 AM - 5:00 PM",
            "tuesday": "8:00 AM - 5:00 PM",
            "wednesday": "8:00 AM - 12:00 PM",
            "thursday": "8:00 AM - 5:00 PM",
            "friday": "8:00 AM - 5:00 PM",
        },
        accepts_new_patients=True,
    ),
    "dr-michael-chen": DoctorProfile(
        id="dr-michael-chen",
        name="Dr. Michael Chen",
        title="MD",
        speciality="Cardiology",
        bio="Dr. Chen specializes in preventive cardiology and is an expert in managing hypertension and heart disease.",
        email="mchen@docseek.com",
        phone="555-0102",
        office_hours={
            "monday": "9:00 AM - 5:00 PM",
            "tuesday": "9:00 AM - 5:00 PM",
            "wednesday": "CLOSED",
            "thursday": "9:00 AM - 5:00 PM",
            "friday": "9:00 AM - 2:00 PM",
        },
        accepts_new_patients=False,
    ),
    "np-emily-rodriguez": DoctorProfile(
        id="np-emily-rodriguez",
        name="Nurse Practitioner Emily Rodriguez",
        title="NP-C",
        speciality="Family Medicine",
        bio="NP Rodriguez provides comprehensive family medicine care including preventive health, minor acute illness, and chronic disease management.",
        email="erodriguez@docseek.com",
        phone="555-0103",
        office_hours={
            "monday": "8:00 AM - 6:00 PM",
            "tuesday": "8:00 AM - 6:00 PM",
            "wednesday": "8:00 AM - 6:00 PM",
            "thursday": "8:00 AM - 6:00 PM",
            "friday": "8:00 AM - 4:00 PM",
        },
        accepts_new_patients=True,
    ),
}


def get_doctor_profile(doctor_id: str) -> Optional[DoctorProfile]:
    """Get a doctor profile by ID.

    Args:
        doctor_id: Doctor profile ID (e.g., 'dr-sarah-johnson')

    Returns:
        DoctorProfile if found, None otherwise
    """
    profile = DOCTOR_PROFILES.get(doctor_id.lower())
    if not profile:
        logger.warning(f"Doctor profile not found: {doctor_id}")
    return profile


def list_doctors() -> List[str]:
    """List all available doctor profile IDs."""
    return list(DOCTOR_PROFILES.keys())


def get_doctor_profile_from_env() -> Optional[DoctorProfile]:
    """Load doctor profile from environment variable.

    Reads DOCTOR_NAME or DOCTOR_ID environment variable.

    Returns:
        DoctorProfile if configured, None otherwise
    """
    import os

    doctor_id = os.getenv("DOCTOR_ID") or os.getenv("DOCTOR_NAME")
    if not doctor_id:
        return None

    return get_doctor_profile(doctor_id)


def load_custom_profiles(config_path: str) -> None:
    """Load additional doctor profiles from a JSON file.

    File format:
        {
            "doctor-id": {
                "name": "Dr. Name",
                "title": "MD",
                "speciality": "Specialty",
                "bio": "Biography...",
                ...
            }
        }

    Args:
        config_path: Path to JSON configuration file
    """
    try:
        path = Path(config_path)
        if not path.exists():
            logger.warning(f"Doctor config file not found: {config_path}")
            return

        with open(path) as f:
            configs = json.load(f)

        for doctor_id, config in configs.items():
            profile = DoctorProfile(
                id=doctor_id,
                name=config["name"],
                title=config["title"],
                speciality=config["speciality"],
                bio=config["bio"],
                email=config.get("email"),
                phone=config.get("phone"),
                office_hours=config.get("office_hours"),
                default_appointment_duration=config.get("default_appointment_duration", 30),
                availability_buffer=config.get("availability_buffer", 15),
                accepts_new_patients=config.get("accepts_new_patients", True),
            )
            DOCTOR_PROFILES[doctor_id] = profile
            logger.info(f"Loaded doctor profile: {doctor_id}")

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse doctor config: {e}")
    except KeyError as e:
        logger.error(f"Missing required field in doctor config: {e}")
