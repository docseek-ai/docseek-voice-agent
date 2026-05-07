"""Medical clinic-specific logic for patient interactions and appointments."""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import json

from docseek_voice_agent.config import settings
from docseek_voice_agent.doctor_config import get_doctor_profile, list_doctors

logger = logging.getLogger(__name__)


@dataclass
class PatientInfo:
    """Minimal patient information for booking."""

    name: str
    phone: str
    email: Optional[str] = None
    date_of_birth: Optional[str] = None
    insurance_provider: Optional[str] = None


@dataclass
class AppointmentSlot:
    """Available appointment time slot."""

    date: str
    time: str
    provider: str
    duration_minutes: int = 30


class MedicalAgentPrompt:
    """System prompts and conversation templates for medical agent."""

    @staticmethod
    def system_prompt(clinic_name: str, doctor_name: Optional[str] = None) -> str:
        """Generate the system prompt for the medical voice agent.

        Args:
            clinic_name: Name of the clinic
            doctor_name: Optional specific doctor name to focus on

        Returns:
            System prompt for the agent
        """
        base_prompt = f"""You are a professional, empathetic medical front desk receptionist for {clinic_name}."""

        if doctor_name:
            base_prompt += f"\n\nYou primarily schedule appointments for {doctor_name}. When patients ask about appointments, \
prioritize {doctor_name}'s availability. If they request a different provider, help them accordingly, but {doctor_name} is your primary focus."

        base_prompt += """

Your responsibilities:
1. Greet patients warmly and professionally
2. Help schedule appointments with available providers
3. Collect necessary patient information (name, phone, reason for visit)
4. Answer basic questions about office hours and services
5. Handle appointment cancellations and rescheduling requests
6. Provide directions and parking information if needed
7. Confirm patient insurance information when relevant

Guidelines:
- Always be warm, empathetic, and professional
- Speak clearly and at a moderate pace
- Ask one question at a time
- Confirm all important details (name, date, time, phone number)
- If you need to put someone on hold, offer a callback instead
- For medical emergencies, recommend calling 911 immediately
- Never provide medical advice - suggest speaking with a provider
- If you don't know the answer to a question, offer to have someone call them back

When scheduling appointments:
- Ask for the patient's preferred dates and times
- Confirm the reason for the visit
- Verify the patient's contact information
- Provide a confirmation number and summary

Be concise but thorough. Aim to complete interactions efficiently while ensuring accuracy."""

        return base_prompt

    @staticmethod
    def doctor_info_prompt(doctor_name: str) -> str:
        """Generate a prompt with doctor information for the agent.

        Args:
            doctor_name: Name of the doctor

        Returns:
            Doctor information prompt or empty string if not found
        """
        # Try to find doctor profile
        for doctor_id in list_doctors():
            profile = get_doctor_profile(doctor_id)
            if profile and profile.name.lower() == doctor_name.lower():
                return f"""Doctor Information:
- Name: {profile.name}, {profile.title}
- Speciality: {profile.speciality}
- Bio: {profile.bio}
- Office Hours: {profile.office_hours or 'Standard clinic hours'}
- Accepting New Patients: {'Yes' if profile.accepts_new_patients else 'No'}
- Contact: {profile.email or 'N/A'} | {profile.phone or 'N/A'}
"""

        return ""

    @staticmethod
    def system_prompt_legacy(clinic_name: str) -> str:
        """Generate the system prompt for the medical voice agent (legacy method)."""
        return f"""You are a professional, empathetic medical front desk receptionist for {clinic_name}.

Your responsibilities:
1. Greet patients warmly and professionally
2. Help schedule appointments with available providers
3. Collect necessary patient information (name, phone, reason for visit)
4. Answer basic questions about office hours and services
5. Handle appointment cancellations and rescheduling requests
6. Provide directions and parking information if needed
7. Confirm patient insurance information when relevant

Guidelines:
- Always be warm, empathetic, and professional
- Speak clearly and at a moderate pace
- Ask one question at a time
- Confirm all important details (name, date, time, phone number)
- If you need to put someone on hold, offer a callback instead
- For medical emergencies, recommend calling 911 immediately
- Never provide medical advice - suggest speaking with a provider
- If you don't know the answer to a question, offer to have someone call them back

When scheduling appointments:
- Ask for the patient's preferred dates and times
- Confirm the reason for the visit
- Verify the patient's contact information
- Provide a confirmation number and summary

Be concise but thorough. Aim to complete interactions efficiently while ensuring accuracy."""

    @staticmethod
    def appointment_confirmation_prompt() -> str:
        """Prompt for confirming appointment details."""
        return """Please confirm the following appointment details:
- Patient Name: {name}
- Phone Number: {phone}
- Appointment Date: {date}
- Appointment Time: {time}
- Reason for Visit: {reason}
- Provider: {provider}

Is everything correct? (yes/no)"""


class AppointmentHandler:
    """Handles appointment scheduling logic."""

    def __init__(self):
        """Initialize appointment handler with mock available slots."""
        self.available_slots = self._generate_available_slots()
        self.booked_appointments = []

    def _generate_available_slots(self) -> list[AppointmentSlot]:
        """Generate mock available appointment slots for the next 30 days."""
        slots = []
        providers = ["Dr. Sarah Johnson", "Dr. Michael Chen", "Nurse Practitioner Emily Rodriguez"]

        for day_offset in range(1, 31):
            date = (datetime.now() + timedelta(days=day_offset)).strftime("%Y-%m-%d")

            # Skip weekends (5=Saturday, 6=Sunday)
            if (datetime.now() + timedelta(days=day_offset)).weekday() >= 5:
                continue

            # Generate slots: 9:00-12:00, 14:00-17:00 (30-min slots)
            times = [
                "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
                "14:00", "14:30", "15:00", "15:30", "16:00", "16:30"
            ]

            for time in times:
                for provider in providers:
                    slots.append(AppointmentSlot(
                        date=date,
                        time=time,
                        provider=provider,
                    ))

        return slots

    async def schedule_appointment(
        self,
        patient_name: str,
        phone: str,
        preferred_date: str,
        preferred_time: str,
        reason: str,
        email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Schedule an appointment for a patient.

        Args:
            patient_name: Full name of the patient
            phone: Contact phone number
            preferred_date: Requested appointment date (YYYY-MM-DD)
            preferred_time: Requested appointment time (HH:MM)
            reason: Reason for the visit
            email: Optional email address

        Returns:
            Dictionary with appointment confirmation details

        Raises:
            ValueError: If the requested slot is unavailable
        """
        # Find available slot matching preferences
        matching_slots = [
            slot for slot in self.available_slots
            if slot.date == preferred_date and slot.time == preferred_time
        ]

        if not matching_slots:
            # Find alternative slots for the same day
            day_slots = [
                slot for slot in self.available_slots
                if slot.date == preferred_date
            ]
            if day_slots:
                raise ValueError(
                    f"That time is not available on {preferred_date}. "
                    f"Available times: {[s.time for s in day_slots[:5]]}"
                )
            else:
                raise ValueError(
                    f"We don't have availability on {preferred_date}. "
                    "Would you like to try a different date?"
                )

        slot = matching_slots[0]

        # Create appointment record
        confirmation_id = f"APP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        appointment = {
            "confirmation_id": confirmation_id,
            "patient_name": patient_name,
            "phone": phone,
            "email": email,
            "date": slot.date,
            "time": slot.time,
            "provider": slot.provider,
            "reason": reason,
            "created_at": datetime.now().isoformat(),
            "status": "confirmed",
        }

        self.booked_appointments.append(appointment)
        logger.info(f"Appointment booked: {confirmation_id} for {patient_name}")

        return appointment

    async def get_available_slots(
        self,
        date: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> list[AppointmentSlot]:
        """Get available appointment slots, optionally filtered."""
        slots = self.available_slots

        if date:
            slots = [s for s in slots if s.date == date]

        if provider:
            slots = [s for s in slots if s.provider == provider]

        return slots

    async def cancel_appointment(self, confirmation_id: str) -> Dict[str, Any]:
        """Cancel an existing appointment."""
        appointment = next(
            (apt for apt in self.booked_appointments if apt["confirmation_id"] == confirmation_id),
            None
        )

        if not appointment:
            raise ValueError(f"Appointment {confirmation_id} not found")

        appointment["status"] = "cancelled"
        logger.info(f"Appointment cancelled: {confirmation_id}")

        return appointment


class PatientIntakeForm:
    """Manages patient intake questionnaire."""

    INTAKE_QUESTIONS = [
        {
            "id": "allergies",
            "question": "Do you have any known allergies to medications or other substances?",
            "type": "text",
        },
        {
            "id": "current_medications",
            "question": "Are you currently taking any medications? If so, which ones?",
            "type": "text",
        },
        {
            "id": "chronic_conditions",
            "question": "Do you have any chronic health conditions like diabetes, hypertension, or asthma?",
            "type": "text",
        },
        {
            "id": "surgery_history",
            "question": "Have you had any major surgeries?",
            "type": "yes_no",
        },
        {
            "id": "family_history",
            "question": "Is there any significant medical history in your family?",
            "type": "text",
        },
    ]

    @staticmethod
    def next_question(completed_questions: list[str]) -> Optional[Dict[str, Any]]:
        """Return the next intake question not yet answered."""
        for q in PatientIntakeForm.INTAKE_QUESTIONS:
            if q["id"] not in completed_questions:
                return q
        return None

    @staticmethod
    def is_intake_complete(completed_questions: list[str]) -> bool:
        """Check if all intake questions have been answered."""
        return len(completed_questions) == len(PatientIntakeForm.INTAKE_QUESTIONS)
