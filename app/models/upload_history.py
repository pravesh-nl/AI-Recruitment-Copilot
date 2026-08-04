from sqlalchemy import Column, Integer, DateTime
from datetime import datetime
from app.database import Base


class UploadHistory(Base):
    __tablename__ = "upload_history"

    id = Column(Integer, primary_key=True, index=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)