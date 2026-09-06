from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database import Base, engine
from app.models.upload_history import UploadHistory
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.interview_session import InterviewSession
from app.models.voice_screening_session import VoiceScreeningSession  # Milestone 4

from app.routes.job import router as job_router
from app.routes.upload import router as upload_router
from app.routes.candidate import router as candidate_router
from app.routes.matching import router as matching_router
from app.routes.interview import router as interview_router
from app.routes.dashboard import router as dashboard_router          # Milestone 4
from app.routes.voice_screening import router as voice_screening_router  # Milestone 4

# Create all tables (existing + new Milestone 4 tables)
Base.metadata.create_all(bind=engine)


# ==============================================================
# Milestone 4 — Safe Database Migration
# Adds recruitment_stage column to existing candidates table.
# Migration is idempotent: silently skips if column already exists.
# Existing records receive the default value "applied".
# No existing columns, rows, or tables are modified or removed.
# ==============================================================
def run_migrations():
    with engine.connect() as conn:
        # ── Milestone 4: recruitment_stage column ──────────────────────────────
        try:
            conn.execute(
                text("ALTER TABLE candidates ADD COLUMN recruitment_stage VARCHAR(30) DEFAULT 'applied'")
            )
            conn.commit()
            print("[Milestone 4 Migration] Added recruitment_stage column to candidates table.")
        except Exception:
            # Column already exists — this is expected after first run
            pass

        # ── Pre-deployment: name_source column ────────────────────────────────
        # Tracks how the candidate name was extracted from the resume.
        # Nullable — existing records receive NULL (treated as "Not Available" by the UI).
        # No existing data is modified or deleted.
        try:
            conn.execute(
                text("ALTER TABLE candidates ADD COLUMN name_source VARCHAR(50)")
            )
            conn.commit()
            print("[Pre-deployment Migration] Added name_source column to candidates table.")
        except Exception:
            # Column already exists — silently skip
            pass


run_migrations()



app = FastAPI(
    title="AI Recruitment Copilot",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://ai-driven-smart-hiring-platform-with-2q4r.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Existing Milestone 1-3 routers (UNCHANGED)
app.include_router(upload_router)
app.include_router(candidate_router)
app.include_router(job_router)
app.include_router(matching_router)
app.include_router(interview_router)

# Milestone 4 routers
app.include_router(dashboard_router)
app.include_router(voice_screening_router)


@app.get("/")
def root():
    return {
        "message": "AI Recruitment Copilot API is running!"
    }
