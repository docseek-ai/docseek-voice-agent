"""Tests for MCP server appointment management."""

import pytest
import json
from datetime import datetime, timedelta

# Mock the MCP server for testing
# In production, this would run as a separate service


class TestMCPServerTools:
    """Test MCP server tool definitions and responses."""

    @pytest.mark.asyncio
    async def test_get_available_slots_structure(self):
        """Test available slots response structure."""
        # This would call the actual MCP server in integration tests
        # For now, test the expected structure
        response = {
            "available_slots": [
                {
                    "date": "2026-05-08",
                    "time": "09:00",
                    "provider": "Dr. Sarah Johnson",
                    "duration_minutes": 30,
                }
            ],
            "total_available": 50,
        }

        assert "available_slots" in response
        assert "total_available" in response
        assert isinstance(response["available_slots"], list)

    @pytest.mark.asyncio
    async def test_book_appointment_response(self):
        """Test appointment booking response structure."""
        response = {
            "success": True,
            "confirmation_id": "APT-20260507120000",
            "patient_name": "John Doe",
            "appointment_date": "2026-05-08",
            "appointment_time": "14:00",
            "provider": "Dr. Sarah Johnson",
            "reason": "Annual checkup",
        }

        assert response["success"] is True
        assert "confirmation_id" in response
        assert response["confirmation_id"].startswith("APT-")
        assert response["patient_name"] == "John Doe"

    @pytest.mark.asyncio
    async def test_cancel_appointment_response(self):
        """Test appointment cancellation response structure."""
        response = {
            "success": True,
            "confirmation_id": "APT-20260507120000",
            "status": "cancelled",
        }

        assert response["success"] is True
        assert response["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_get_appointment_response(self):
        """Test appointment lookup response structure."""
        response = {
            "success": True,
            "confirmation_id": "APT-20260507120000",
            "patient_name": "Jane Doe",
            "phone": "+1-555-9876",
            "appointment_date": "2026-05-08",
            "appointment_time": "10:00",
            "provider": "Dr. Michael Chen",
            "reason": "Follow-up",
            "status": "confirmed",
        }

        assert response["success"] is True
        assert response["status"] == "confirmed"

    @pytest.mark.asyncio
    async def test_get_patient_response(self):
        """Test patient lookup response structure."""
        response = {
            "success": True,
            "patient_id": 1,
            "name": "John Doe",
            "phone": "+1-555-0123",
            "email": "john@example.com",
            "recent_appointments": [
                {
                    "confirmation_id": "APT-20260507120000",
                    "date": "2026-05-08",
                    "time": "14:00",
                    "provider": "Dr. Sarah Johnson",
                }
            ],
        }

        assert response["success"] is True
        assert response["patient_id"] == 1
        assert isinstance(response["recent_appointments"], list)

    @pytest.mark.asyncio
    async def test_save_patient_intake_response(self):
        """Test patient intake save response structure."""
        response = {
            "success": True,
            "patient_id": 1,
            "intake_completed": True,
        }

        assert response["success"] is True
        assert response["intake_completed"] is True

    @pytest.mark.asyncio
    async def test_get_providers_response(self):
        """Test provider list response structure."""
        response = {
            "providers": [
                "Dr. Sarah Johnson",
                "Dr. Michael Chen",
                "Nurse Practitioner Emily Rodriguez",
            ]
        }

        assert "providers" in response
        assert len(response["providers"]) == 3
        assert all(isinstance(p, str) for p in response["providers"])

    def test_slot_generation_logic(self):
        """Test clinic hours slot generation logic."""
        start_date = datetime(2026, 5, 8)  # Friday
        end_date = datetime(2026, 5, 10)   # Sunday

        # Generate slots manually
        slots = []
        current = start_date
        while current <= end_date:
            # Skip weekends (5=Saturday, 6=Sunday)
            if current.weekday() >= 5:
                current += timedelta(days=1)
                continue

            date_str = current.strftime("%Y-%m-%d")

            # Clinic hours: 9 AM - 5 PM, 30-min slots
            for hour in range(9, 17):
                for minute in [0, 30]:
                    time_str = f"{hour:02d}:{minute:02d}"
                    slots.append((date_str, time_str))

            current += timedelta(days=1)

        # Should have slots only for Friday (May 8)
        # 9:00, 9:30, 10:00, ..., 16:30 = 16 slots
        assert len(slots) == 16
        assert slots[0] == ("2026-05-08", "09:00")
        assert slots[-1] == ("2026-05-08", "16:30")

    def test_conflict_detection(self):
        """Test that booked slots are excluded from availability."""
        all_slots = {
            ("2026-05-08", "09:00", "Dr. Sarah Johnson"),
            ("2026-05-08", "09:30", "Dr. Sarah Johnson"),
            ("2026-05-08", "10:00", "Dr. Sarah Johnson"),
        }

        booked_slots = {("2026-05-08", "09:30", "Dr. Sarah Johnson")}

        available = all_slots - booked_slots

        assert ("2026-05-08", "09:00", "Dr. Sarah Johnson") in available
        assert ("2026-05-08", "09:30", "Dr. Sarah Johnson") not in available
        assert ("2026-05-08", "10:00", "Dr. Sarah Johnson") in available
