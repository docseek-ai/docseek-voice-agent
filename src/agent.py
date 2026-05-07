#!/usr/bin/env python3
"""
DocSeek Medical Front Desk Voice Agent

A realtime voice agent for appointment scheduling, patient intake, and medical office support.
Handles patient inquiries, books appointments, and captures basic patient information.

Usage:
    python src/agent.py console       # Interactive console mode
    python src/agent.py dev           # Development with hot reload
    python src/agent.py start         # Production mode
    python src/agent.py download-files # Download required models
"""

import asyncio
import logging
import sys
from pathlib import Path

from livekit.agents import (
    AgentContext,
    AgentServer,
    JobRequest,
    VoicePipelineAgent,
    cli,
)
from livekit.agents.llm import ChatMessage, ChatContext
from livekit.agents.silero import VAD
from livekit.agents.turn_detector import EOUDetector
from livekit import api

# Import medical-specific logic
from docseek_voice_agent.config import settings
from docseek_voice_agent.clinic_logic import MedicalAgentPrompt, AppointmentHandler

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class MedicalFrontDeskAgent:
    """Main agent for medical office voice interactions."""

    def __init__(self, ctx: AgentContext):
        self.ctx = ctx
        self.appointment_handler = AppointmentHandler()
        self.chat_history: list[ChatMessage] = []

    async def on_message_received(self, message: str) -> None:
        """Handle incoming user messages and maintain conversation context."""
        logger.info(f"User message: {message}")

        # Add to chat history
        self.chat_history.append(
            ChatMessage(role="user", content=message)
        )

    async def on_appointment_request(self, details: dict) -> str:
        """Handle appointment booking requests."""
        try:
            result = await self.appointment_handler.schedule_appointment(
                patient_name=details.get("name"),
                phone=details.get("phone"),
                preferred_date=details.get("date"),
                preferred_time=details.get("time"),
                reason=details.get("reason"),
            )
            logger.info(f"Appointment scheduled: {result}")
            return f"I've scheduled your appointment for {result['date']} at {result['time']}. Your confirmation number is {result['confirmation_id']}."
        except Exception as e:
            logger.error(f"Failed to schedule appointment: {e}")
            return "I'm having trouble scheduling that appointment right now. Could you please call us directly at " + settings.clinic_phone + "?"


async def prewarm_process(proc: JobRequest) -> None:
    """Prewarm model downloads before agent starts."""
    logger.info("Prewarming speech models...")
    await proc.aqueue.put(None)


async def entrypoint(ctx: AgentContext):
    """Main entrypoint for the voice agent session."""
    logger.info(f"Starting medical front desk agent in room: {ctx.room.name}")

    # Initialize medical agent
    medical_agent = MedicalFrontDeskAgent(ctx)

    # Get speech and LLM configurations from settings
    stt_model = settings.stt_provider
    llm_model = settings.llm_model
    tts_voice = settings.tts_voice

    logger.info(f"Using STT: {stt_model}, LLM: {llm_model}, TTS: {tts_voice}")

    # Create the voice pipeline with medical context
    initial_ctx = ChatContext(
        messages=[
            ChatMessage(
                role="system",
                content=MedicalAgentPrompt.system_prompt(settings.clinic_name),
            ),
        ]
    )

    agent = VoicePipelineAgent(
        ctx=ctx,
        vad=VAD.create(),
        stt=None,  # Uses LiveKit's default STT from provider
        llm=None,  # Uses LiveKit's default LLM from provider
        tts=None,  # Uses LiveKit's default TTS from provider
        chat_ctx=initial_ctx,
    )

    agent.start(ctx.room, ctx.participant)

    # Welcome greeting
    await agent.say(
        f"Hello! Thank you for calling {settings.clinic_name}. "
        "How can I help you today? Are you looking to schedule an appointment or do you have a question?",
        allow_interruptions=True,
    )

    logger.info("Agent started and ready for interactions")


# Initialize LiveKit Agent Server
app = AgentServer()
app.on_job_request(entrypoint)
app.on_prewarm(prewarm_process)


def main():
    """CLI entry point."""
    cli.run_app(app)


if __name__ == "__main__":
    main()
