"""
Database connection, session management, and initialization.
Supports PostgreSQL for staging/production and SQLite for local development.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from config.settings import settings
from backend.database.models import Base, Doctor

# Configure connect_args based on DB dialect (SQLite needs check_same_thread=False)
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency to yield database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables and seed baseline clinic fixtures."""
    Base.metadata.create_all(bind=engine)

    # Seed baseline doctors if table is empty
    with SessionLocal() as db:
        if db.query(Doctor).count() == 0:
            doctors = [
                Doctor(
                    doctor_id="DOC-001",
                    doctor_name="Dr. Ahmed Khan",
                    specialization="General Physician",
                    calendar_id="primary",
                    timezone=settings.CLINIC_TIMEZONE,
                    active_status=True,
                    working_hours_start="09:00",
                    working_hours_end="17:00",
                ),
                Doctor(
                    doctor_id="DOC-002",
                    doctor_name="Dr. Sarah Patel",
                    specialization="Dermatologist",
                    calendar_id="primary",
                    timezone=settings.CLINIC_TIMEZONE,
                    active_status=True,
                    working_hours_start="10:00",
                    working_hours_end="16:00",
                ),
                Doctor(
                    doctor_id="DOC-003",
                    doctor_name="Dr. Michael Chen",
                    specialization="Cardiologist",
                    calendar_id="primary",
                    timezone=settings.CLINIC_TIMEZONE,
                    active_status=True,
                    working_hours_start="09:00",
                    working_hours_end="15:00",
                ),
            ]
            db.add_all(doctors)
            db.commit()

