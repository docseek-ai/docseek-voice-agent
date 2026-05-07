"""MCP Server for DocSeek Voice Agent - Database and Appointment Management

This server exposes the voice agent's database operations as MCP tools.
Allows the agent to query availability, book appointments, manage patients, etc.

Run: python -m mcp_server.mcp_server
Or use with Claude Code via MCP client configuration.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent, ToolResult

from docseek_voice_agent.config import settings
from docseek_voice_agent.database import (
    SessionLocal,
    Patient,
    Appointment,
    PatientIntakeRecord,
    init_db,
)

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, settings.log_level.upper()))

# Initialize database
init_db()

# Create MCP server
server = Server(name="docseek-voice-agent")


# ============================================================================
# Tool Definitions
# ============================================================================


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools for the voice agent."""
    return [
        Tool(
            name="get_available_slots",
            description="Get available appointment slots for a given date range and provider",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date (YYYY-MM-DD)",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date (YYYY-MM-DD)",
                    },
                    "provider": {
                        "type": "string",
                        "description": "Provider name (optional, leave empty for all)",
                    },
                },
                "required": ["start_date", "end_date"],
            },
        ),
        Tool(
            name="book_appointment",
            description="Book an appointment for a patient",
            inputSchema={
                "type": "object",
                "properties": {
                    "patient_name": {
                        "type": "string",
                        "description": "Full name of patient",
                    },
                    "phone": {
                        "type": "string",
                        "description": "Patient phone number",
                    },
                    "email": {
                        "type": "string",
                        "description": "Patient email (optional)",
                    },
                    "appointment_date": {
                        "type": "string",
                        "description": "Appointment date (YYYY-MM-DD)",
                    },
                    "appointment_time": {
                        "type": "string",
                        "description": "Appointment time (HH:MM)",
                    },
                    "provider": {
                        "type": "string",
                        "description": "Provider name",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for visit",
                    },
                },
                "required": [
                    "patient_name",
                    "phone",
                    "appointment_date",
                    "appointment_time",
                    "provider",
                    "reason",
                ],
            },
        ),
        Tool(
            name="cancel_appointment",
            description="Cancel an existing appointment",
            inputSchema={
                "type": "object",
                "properties": {
                    "confirmation_id": {
                        "type": "string",
                        "description": "Appointment confirmation ID",
                    },
                },
                "required": ["confirmation_id"],
            },
        ),
        Tool(
            name="get_appointment",
            description="Look up an appointment by confirmation ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "confirmation_id": {
                        "type": "string",
                        "description": "Appointment confirmation ID",
                    },
                },
                "required": ["confirmation_id"],
            },
        ),
        Tool(
            name="get_patient",
            description="Look up patient information by phone number",
            inputSchema={
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "description": "Patient phone number",
                    },
                },
                "required": ["phone"],
            },
        ),
        Tool(
            name="save_patient_intake",
            description="Save patient intake form responses",
            inputSchema={
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "description": "Patient phone number",
                    },
                    "allergies": {
                        "type": "string",
                        "description": "Known allergies",
                    },
                    "current_medications": {
                        "type": "string",
                        "description": "Current medications",
                    },
                    "chronic_conditions": {
                        "type": "string",
                        "description": "Chronic conditions",
                    },
                    "surgery_history": {
                        "type": "boolean",
                        "description": "Has had surgery",
                    },
                    "family_history": {
                        "type": "string",
                        "description": "Family medical history",
                    },
                },
                "required": ["phone"],
            },
        ),
        Tool(
            name="get_providers",
            description="Get list of available providers",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
    ]


# ============================================================================
# Tool Implementations
# ============================================================================


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute a tool and return results."""
    try:
        if name == "get_available_slots":
            return await _get_available_slots(arguments)
        elif name == "book_appointment":
            return await _book_appointment(arguments)
        elif name == "cancel_appointment":
            return await _cancel_appointment(arguments)
        elif name == "get_appointment":
            return await _get_appointment(arguments)
        elif name == "get_patient":
            return await _get_patient(arguments)
        elif name == "save_patient_intake":
            return await _save_patient_intake(arguments)
        elif name == "get_providers":
            return await _get_providers(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        logger.error(f"Tool error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def _get_available_slots(args: dict) -> list[TextContent]:
    """Get available appointment slots."""
    db = SessionLocal()
    try:
        start_date = datetime.strptime(args["start_date"], "%Y-%m-%d")
        end_date = datetime.strptime(args["end_date"], "%Y-%m-%d")
        provider_filter = args.get("provider", "")

        # Get all appointments in date range
        booked = db.query(Appointment).filter(
            Appointment.appointment_date >= args["start_date"],
            Appointment.appointment_date <= args["end_date"],
            Appointment.status == "confirmed",
        )

        if provider_filter:
            booked = booked.filter(Appointment.provider == provider_filter)

        booked_slots = set()
        for apt in booked.all():
            booked_slots.add((apt.appointment_date, apt.appointment_time, apt.provider))

        # Generate available slots (hardcoded clinic hours)
        available = []
        current = start_date
        while current <= end_date:
            # Skip weekends
            if current.weekday() >= 5:
                current += timedelta(days=1)
                continue

            date_str = current.strftime("%Y-%m-%d")
            providers = [
                "Dr. Sarah Johnson",
                "Dr. Michael Chen",
                "Nurse Practitioner Emily Rodriguez",
            ]

            # Clinic hours: 9 AM - 5 PM, 30-min slots
            for hour in range(9, 17):
                for minute in [0, 30]:
                    time_str = f"{hour:02d}:{minute:02d}"

                    for provider in providers:
                        if provider_filter and provider != provider_filter:
                            continue

                        if (date_str, time_str, provider) not in booked_slots:
                            available.append(
                                {
                                    "date": date_str,
                                    "time": time_str,
                                    "provider": provider,
                                    "duration_minutes": 30,
                                }
                            )

            current += timedelta(days=1)

        result = {
            "available_slots": available[:50],  # Limit to 50 for readability
            "total_available": len(available),
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    finally:
        db.close()


async def _book_appointment(args: dict) -> list[TextContent]:
    """Book an appointment for a patient."""
    db = SessionLocal()
    try:
        # Check if slot is available
        existing = db.query(Appointment).filter(
            Appointment.appointment_date == args["appointment_date"],
            Appointment.appointment_time == args["appointment_time"],
            Appointment.provider == args["provider"],
            Appointment.status == "confirmed",
        ).first()

        if existing:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": False,
                            "error": f"Slot {args['appointment_date']} at {args['appointment_time']} with {args['provider']} is already booked",
                        }
                    ),
                )
            ]

        # Create or update patient
        patient = db.query(Patient).filter(Patient.phone == args["phone"]).first()
        if not patient:
            patient = Patient(
                name=args["patient_name"],
                phone=args["phone"],
                email=args.get("email"),
            )
            db.add(patient)
            db.flush()

        # Create appointment
        confirmation_id = f"APT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        appointment = Appointment(
            confirmation_id=confirmation_id,
            patient_id=patient.id,
            patient_name=args["patient_name"],
            phone=args["phone"],
            appointment_date=args["appointment_date"],
            appointment_time=args["appointment_time"],
            provider=args["provider"],
            reason=args["reason"],
            status="confirmed",
        )
        db.add(appointment)
        db.commit()

        logger.info(f"Appointment booked: {confirmation_id}")

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "success": True,
                        "confirmation_id": confirmation_id,
                        "patient_name": args["patient_name"],
                        "appointment_date": args["appointment_date"],
                        "appointment_time": args["appointment_time"],
                        "provider": args["provider"],
                        "reason": args["reason"],
                    }
                ),
            )
        ]

    except Exception as e:
        db.rollback()
        logger.error(f"Booking error: {e}")
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "success": False,
                        "error": str(e),
                    }
                ),
            )
        ]
    finally:
        db.close()


async def _cancel_appointment(args: dict) -> list[TextContent]:
    """Cancel an appointment."""
    db = SessionLocal()
    try:
        appointment = db.query(Appointment).filter(
            Appointment.confirmation_id == args["confirmation_id"]
        ).first()

        if not appointment:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": False,
                            "error": f"Appointment {args['confirmation_id']} not found",
                        }
                    ),
                )
            ]

        appointment.status = "cancelled"
        db.commit()

        logger.info(f"Appointment cancelled: {args['confirmation_id']}")

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "success": True,
                        "confirmation_id": args["confirmation_id"],
                        "status": "cancelled",
                    }
                ),
            )
        ]

    except Exception as e:
        db.rollback()
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "success": False,
                        "error": str(e),
                    }
                ),
            )
        ]
    finally:
        db.close()


async def _get_appointment(args: dict) -> list[TextContent]:
    """Look up appointment by confirmation ID."""
    db = SessionLocal()
    try:
        appointment = db.query(Appointment).filter(
            Appointment.confirmation_id == args["confirmation_id"]
        ).first()

        if not appointment:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": False,
                            "error": f"Appointment {args['confirmation_id']} not found",
                        }
                    ),
                )
            ]

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "success": True,
                        "confirmation_id": appointment.confirmation_id,
                        "patient_name": appointment.patient_name,
                        "phone": appointment.phone,
                        "appointment_date": appointment.appointment_date,
                        "appointment_time": appointment.appointment_time,
                        "provider": appointment.provider,
                        "reason": appointment.reason,
                        "status": appointment.status,
                    }
                ),
            )
        ]

    finally:
        db.close()


async def _get_patient(args: dict) -> list[TextContent]:
    """Look up patient by phone number."""
    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.phone == args["phone"]).first()

        if not patient:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": False,
                            "error": f"Patient {args['phone']} not found",
                        }
                    ),
                )
            ]

        # Get recent appointments
        appointments = (
            db.query(Appointment)
            .filter(
                Appointment.patient_id == patient.id, Appointment.status == "confirmed"
            )
            .order_by(Appointment.appointment_date.desc())
            .limit(5)
            .all()
        )

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "success": True,
                        "patient_id": patient.id,
                        "name": patient.name,
                        "phone": patient.phone,
                        "email": patient.email,
                        "recent_appointments": [
                            {
                                "confirmation_id": apt.confirmation_id,
                                "date": apt.appointment_date,
                                "time": apt.appointment_time,
                                "provider": apt.provider,
                            }
                            for apt in appointments
                        ],
                    }
                ),
            )
        ]

    finally:
        db.close()


async def _save_patient_intake(args: dict) -> list[TextContent]:
    """Save patient intake form responses."""
    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.phone == args["phone"]).first()

        if not patient:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": False,
                            "error": f"Patient {args['phone']} not found. Create patient first.",
                        }
                    ),
                )
            ]

        # Create or update intake record
        intake = db.query(PatientIntakeRecord).filter(
            PatientIntakeRecord.patient_id == patient.id
        ).first()

        if not intake:
            intake = PatientIntakeRecord(patient_id=patient.id)

        intake.allergies = args.get("allergies")
        intake.current_medications = args.get("current_medications")
        intake.chronic_conditions = args.get("chronic_conditions")
        intake.surgery_history = args.get("surgery_history")
        intake.family_history = args.get("family_history")
        intake.completed = True

        db.add(intake)
        db.commit()

        logger.info(f"Intake saved for patient {args['phone']}")

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "success": True,
                        "patient_id": patient.id,
                        "intake_completed": True,
                    }
                ),
            )
        ]

    except Exception as e:
        db.rollback()
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "success": False,
                        "error": str(e),
                    }
                ),
            )
        ]
    finally:
        db.close()


async def _get_providers(args: dict) -> list[TextContent]:
    """Get list of available providers."""
    providers = [
        "Dr. Sarah Johnson",
        "Dr. Michael Chen",
        "Nurse Practitioner Emily Rodriguez",
    ]
    return [
        TextContent(
            type="text",
            text=json.dumps(
                {
                    "providers": providers,
                }
            ),
        )
    ]


# ============================================================================
# Server Lifecycle
# ============================================================================


async def main():
    """Run the MCP server."""
    import asyncio

    async with server:
        logger.info("DocSeek Voice Agent MCP Server started")
        await asyncio.sleep(float("inf"))


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
