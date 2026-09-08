from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.database import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=True)
    # Tracks how the candidate name was extracted from the resume.
    # Values: "Explicit Name Field" | "Resume Header" | "NER / Name Extraction" | "Not Available"
    # Nullable — existing records before this migration will have NULL (treated as "Not Available").
    name_source = Column(String(50), nullable=True)
    email = Column(String(100), unique=True, nullable=True)
    phone = Column(String(20), nullable=True)

    education = Column(Text, nullable=True)
    skills = Column(Text, nullable=True)
    certifications = Column(Text, nullable=True)
    projects = Column(Text, nullable=True)
    experience = Column(Text, nullable=True)

    resume_path = Column(String(255), nullable=True)

    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Milestone 4: Recruitment pipeline stage tracking
    # Valid values: applied | screened | interviewed | offered | hired
    # Added via safe ALTER TABLE migration in main.py — existing records default to "applied"
    recruitment_stage = Column(String(30), nullable=True, default="applied")
    
    # Recruiter Hiring Decision
    # Valid values: IN_PROGRESS | HIRED | NOT_SELECTED | NOT_EVALUATED
    hiring_status = Column(String(50), nullable=True, default="IN_PROGRESS")