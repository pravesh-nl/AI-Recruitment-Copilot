from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime
from app.database import Base


class VoiceScreeningSession(Base):
    __tablename__ = "voice_screening_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), unique=True, index=True, nullable=False)

    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)

    # JSON array of {role: "ai"|"candidate", content: "..."}
    transcript = Column(Text, nullable=False, default="[]")

    status = Column(String(20), nullable=False, default="active")  # active / completed

    # Structured JSON assessment from AI
    assessment = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
