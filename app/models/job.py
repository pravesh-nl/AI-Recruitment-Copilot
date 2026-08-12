from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(150), nullable=False)

    min_experience = Column(Integer, default=0)

    # Stored as JSON string
    skills = Column(Text, nullable=False)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )