"""Configuration management for the medical voice agent."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # LiveKit Configuration
    livekit_url: str = Field(default="ws://localhost:7880")
    livekit_api_key: str = Field(default="")
    livekit_api_secret: str = Field(default="")

    # Speech-to-Text (STT)
    stt_provider: str = Field(default="deepgram/nova-3:multi")

    # Large Language Model (LLM)
    llm_model: str = Field(default="openai/gpt-4o-mini")
    openai_api_key: str = Field(default="")

    # Text-to-Speech (TTS)
    tts_provider: str = Field(default="openai")
    tts_voice: str = Field(default="alloy")

    # Deepgram API (for advanced STT)
    deepgram_api_key: str = Field(default="")

    # Google API (optional, for additional services)
    google_api_key: str = Field(default="")

    # Database Configuration
    database_url: str = Field(default="sqlite:///./docseek_voice.db")

    # Agent Configuration
    agent_name: str = Field(default="docseek-front-desk")
    log_level: str = Field(default="info")

    # Clinic Profile Configuration (RECOMMENDED)
    # Set CLINIC_ID to load all clinic settings (name, phone, address, doctors, hours)
    clinic_id: Optional[str] = Field(default=None)

    # Fallback: Manual Clinic Settings (used if CLINIC_ID not set)
    clinic_name: str = Field(default="DocSeek Medical")
    clinic_timezone: str = Field(default="America/Chicago")
    clinic_phone: str = Field(default="+1-555-0123")
    clinic_address: str = Field(default="")

    # Doctor-Specific Configuration (optional)
    # If set, agent focuses on this doctor's schedule
    doctor_id: Optional[str] = Field(default=None)

    # Agent Behavior
    enable_appointment_booking: bool = Field(default=True)
    enable_patient_intake: bool = Field(default=True)
    max_conversation_duration: int = Field(default=600)  # seconds

    class Config:
        env_file = ".env.local"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
