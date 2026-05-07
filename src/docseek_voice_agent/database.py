"""Database models and session management for appointments and patient records."""

from sqlalchemy import create_engine, Column, String, DateTime, Integer, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import Optional

from docseek_voice_agent.config import settings

# Create database engine and session
engine = create_engine(settings.database_url, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Patient(Base):
    """Patient record."""

    __tablename__ = "patients"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False, unique=True)
    email = Column(String(255), nullable=True)
    date_of_birth = Column(String(10), nullable=True)
    insurance_provider = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Appointment(Base):
    """Appointment record."""

    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True)
    confirmation_id = Column(String(50), unique=True, nullable=False)
    patient_id = Column(Integer, nullable=False)
    patient_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    appointment_date = Column(String(10), nullable=False)
    appointment_time = Column(String(5), nullable=False)
    provider = Column(String(255), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(20), default="confirmed")  # confirmed, cancelled, completed, no-show
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PatientIntakeRecord(Base):
    """Patient intake form responses."""

    __tablename__ = "patient_intake"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, nullable=False)
    appointment_id = Column(Integer, nullable=True)
    allergies = Column(Text, nullable=True)
    current_medications = Column(Text, nullable=True)
    chronic_conditions = Column(Text, nullable=True)
    surgery_history = Column(Boolean, nullable=True)
    family_history = Column(Text, nullable=True)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PhoneSession(Base):
    """Track voice agent phone sessions."""

    __tablename__ = "phone_sessions"

    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), unique=True, nullable=False)
    caller_phone = Column(String(20), nullable=True)
    room_name = Column(String(255), nullable=True)
    status = Column(String(20), default="active")  # active, completed, disconnected
    duration_seconds = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
