"""Tests for medical clinic logic."""

import pytest
from datetime import datetime, timedelta
from docseek_voice_agent.clinic_logic import (
    AppointmentHandler,
    MedicalAgentPrompt,
    PatientIntakeForm,
)


@pytest.fixture
def appointment_handler():
    """Create an appointment handler for testing."""
    return AppointmentHandler()


class TestMedicalAgentPrompt:
    """Test system prompts and message templates."""

    def test_system_prompt_includes_clinic_name(self):
        """Verify system prompt includes the clinic name."""
        clinic_name = "Test Medical Clinic"
        prompt = MedicalAgentPrompt.system_prompt(clinic_name)

        assert clinic_name in prompt
        assert "receptionist" in prompt.lower()
        assert "appointment" in prompt.lower()

    def test_confirmation_prompt_has_required_fields(self):
        """Verify confirmation prompt template includes all fields."""
        prompt = MedicalAgentPrompt.appointment_confirmation_prompt()

        required_fields = ["{name}", "{phone}", "{date}", "{time}", "{reason}", "{provider}"]
        for field in required_fields:
            assert field in prompt


class TestAppointmentHandler:
    """Test appointment scheduling logic."""

    def test_available_slots_generated(self, appointment_handler):
        """Verify available slots are generated on initialization."""
        assert len(appointment_handler.available_slots) > 0

    def test_no_weekend_slots(self, appointment_handler):
        """Verify no appointments on weekends."""
        for slot in appointment_handler.available_slots:
            date = datetime.strptime(slot.date, "%Y-%m-%d")
            # 5 = Saturday, 6 = Sunday
            assert date.weekday() < 5, f"Found weekend slot: {slot.date}"

    @pytest.mark.asyncio
    async def test_schedule_appointment(self, appointment_handler):
        """Test successful appointment scheduling."""
        slots = appointment_handler.available_slots
        assert len(slots) > 0

        slot = slots[0]
        result = await appointment_handler.schedule_appointment(
            patient_name="John Doe",
            phone="+1-555-0123",
            preferred_date=slot.date,
            preferred_time=slot.time,
            reason="Routine checkup",
        )

        assert result["confirmation_id"]
        assert result["patient_name"] == "John Doe"
        assert result["date"] == slot.date
        assert result["time"] == slot.time
        assert result["status"] == "confirmed"

    @pytest.mark.asyncio
    async def test_schedule_appointment_invalid_slot(self, appointment_handler):
        """Test scheduling with invalid date/time."""
        with pytest.raises(ValueError):
            await appointment_handler.schedule_appointment(
                patient_name="John Doe",
                phone="+1-555-0123",
                preferred_date="2099-12-31",  # Far in future, no slots
                preferred_time="09:00",
                reason="Checkup",
            )

    @pytest.mark.asyncio
    async def test_get_available_slots(self, appointment_handler):
        """Test filtering available slots."""
        slots = await appointment_handler.get_available_slots()
        assert len(slots) > 0

    @pytest.mark.asyncio
    async def test_cancel_appointment(self, appointment_handler):
        """Test appointment cancellation."""
        # First, schedule an appointment
        slots = appointment_handler.available_slots
        slot = slots[0]

        result = await appointment_handler.schedule_appointment(
            patient_name="Jane Doe",
            phone="+1-555-9999",
            preferred_date=slot.date,
            preferred_time=slot.time,
            reason="Follow-up visit",
        )

        confirmation_id = result["confirmation_id"]

        # Then cancel it
        cancelled = await appointment_handler.cancel_appointment(confirmation_id)
        assert cancelled["status"] == "cancelled"


class TestPatientIntakeForm:
    """Test patient intake questionnaire."""

    def test_intake_questions_exist(self):
        """Verify intake questions are defined."""
        assert len(PatientIntakeForm.INTAKE_QUESTIONS) > 0

    def test_first_question(self):
        """Test getting the first intake question."""
        question = PatientIntakeForm.next_question([])
        assert question is not None
        assert question["id"] == "allergies"

    def test_next_question_progression(self):
        """Test question progression."""
        completed = ["allergies"]
        question = PatientIntakeForm.next_question(completed)
        assert question is not None
        assert question["id"] == "current_medications"

    def test_intake_completion(self):
        """Test intake completion check."""
        completed_ids = [q["id"] for q in PatientIntakeForm.INTAKE_QUESTIONS]

        assert not PatientIntakeForm.is_intake_complete([])
        assert not PatientIntakeForm.is_intake_complete(completed_ids[:-1])
        assert PatientIntakeForm.is_intake_complete(completed_ids)
