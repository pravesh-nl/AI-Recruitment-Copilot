"""
Voice Screening Routes — Milestone 4
POST /voice-screening/start              — Start a voice screening session
POST /voice-screening/{session_id}/respond — Submit candidate speech transcript, receive next AI question
POST /voice-screening/{session_id}/end   — End session and generate structured assessment
GET  /voice-screening/{session_id}       — Retrieve session data (transcript + assessment)

These routes are isolated. Failure here does NOT affect:
  - Existing interview simulation
  - ATS status
  - Candidate matching
  - Dashboard
"""

import json
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import SessionLocal
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.voice_screening_session import VoiceScreeningSession
from app.services.voice_screening_service import (
    generate_screening_question,
    generate_screening_assessment
)

router = APIRouter(
    prefix="/voice-screening",
    tags=["Voice Screening"]
)


class StartScreeningRequest(BaseModel):
    candidate_id: int
    job_id: int


class RespondRequest(BaseModel):
    transcript: str


@router.post("/start")
def start_screening(request: StartScreeningRequest):
    """
    Start a new voice screening session.
    Returns the first AI screening question and a session_id.
    """
    db = SessionLocal()
    try:
        candidate = db.query(Candidate).filter(Candidate.id == request.candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        job = db.query(Job).filter(Job.id == request.job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        job_skills = json.loads(job.skills or "[]")

        # Generate the first AI question — may raise on Groq 429
        try:
            first_question = generate_screening_question(
                job_title=job.title,
                job_skills=job_skills,
                candidate_name=candidate.name or "Candidate",
                candidate_skills=candidate.skills or "Not specified",
                conversation_history=[]
            )
        except Exception as ai_err:
            raise HTTPException(status_code=503, detail=str(ai_err))

        session_id = str(uuid.uuid4())
        initial_transcript = [{"role": "ai", "content": first_question}]

        session = VoiceScreeningSession(
            session_id=session_id,
            candidate_id=candidate.id,
            job_id=job.id,
            transcript=json.dumps(initial_transcript),
            status="active"
        )
        db.add(session)
        db.commit()

        return {
            "session_id": session_id,
            "first_question": first_question,
            "candidate_name": candidate.name or "Candidate",
            "job_title": job.title
        }

    finally:
        db.close()


@router.post("/{session_id}/respond")
def respond_to_screening(session_id: str, request: RespondRequest):
    """
    Submit the candidate's spoken response and receive the next AI question.
    Transcript is saved to DB even if AI fails to generate the next question.
    """
    db = SessionLocal()
    try:
        session = (
            db.query(VoiceScreeningSession)
            .filter(VoiceScreeningSession.session_id == session_id)
            .first()
        )
        if not session:
            raise HTTPException(status_code=404, detail="Screening session not found")

        if session.status != "active":
            raise HTTPException(status_code=400, detail="Screening session is already completed")

        candidate_text = (request.transcript or "").strip()
        if not candidate_text:
            raise HTTPException(status_code=400, detail="Transcript cannot be empty")

        job = db.query(Job).filter(Job.id == session.job_id).first()
        candidate = db.query(Candidate).filter(Candidate.id == session.candidate_id).first()

        # Load current transcript and append candidate turn
        conversation = json.loads(session.transcript)
        conversation.append({"role": "candidate", "content": candidate_text})

        job_skills = json.loads(job.skills or "[]") if job else []

        # Generate next AI question — save transcript first even on AI failure
        try:
            next_question = generate_screening_question(
                job_title=job.title if job else "Unknown",
                job_skills=job_skills,
                candidate_name=candidate.name if candidate else "Candidate",
                candidate_skills=candidate.skills if candidate else "Not specified",
                conversation_history=conversation
            )
            conversation.append({"role": "ai", "content": next_question})
            session.transcript = json.dumps(conversation)
            db.commit()
            return {
                "next_question": next_question,
                "candidate_turns": sum(1 for t in conversation if t["role"] == "candidate")
            }
        except Exception as ai_err:
            # Save transcript progress even on AI failure
            session.transcript = json.dumps(conversation)
            db.commit()
            raise HTTPException(status_code=503, detail=str(ai_err))

    finally:
        db.close()


@router.post("/{session_id}/end")
def end_screening(session_id: str):
    """
    End the voice screening and generate a structured assessment.
    If the session was already completed, returns the existing assessment.
    Assessment generation failure returns a safe fallback — never HTTP 500.
    """
    db = SessionLocal()
    try:
        session = (
            db.query(VoiceScreeningSession)
            .filter(VoiceScreeningSession.session_id == session_id)
            .first()
        )
        if not session:
            raise HTTPException(status_code=404, detail="Screening session not found")

        # Already completed — return existing assessment
        if session.status == "completed":
            existing_assessment = {}
            if session.assessment:
                try:
                    existing_assessment = json.loads(session.assessment)
                except Exception:
                    pass
            return {
                "message": "Screening already completed",
                "assessment": existing_assessment,
                "session_id": session_id
            }

        job = db.query(Job).filter(Job.id == session.job_id).first()
        candidate = db.query(Candidate).filter(Candidate.id == session.candidate_id).first()

        transcript = json.loads(session.transcript)
        job_skills = json.loads(job.skills or "[]") if job else []

        # generate_screening_assessment never raises — returns fallback on failure
        assessment = generate_screening_assessment(
            job_title=job.title if job else "Unknown",
            job_skills=job_skills,
            candidate_name=candidate.name if candidate else "Candidate",
            candidate_skills=candidate.skills if candidate else "Not specified",
            transcript=transcript
        )

        session.status = "completed"
        session.assessment = json.dumps(assessment)
        db.commit()

        return {
            "message": "Screening completed",
            "assessment": assessment,
            "session_id": session_id
        }

    finally:
        db.close()


@router.get("/{session_id}")
def get_screening_session(session_id: str):
    """Retrieve a voice screening session with its transcript and assessment."""
    db = SessionLocal()
    try:
        session = (
            db.query(VoiceScreeningSession)
            .filter(VoiceScreeningSession.session_id == session_id)
            .first()
        )
        if not session:
            raise HTTPException(status_code=404, detail="Screening session not found")

        assessment = None
        if session.assessment:
            try:
                assessment = json.loads(session.assessment)
            except Exception:
                pass

        transcript = []
        try:
            transcript = json.loads(session.transcript)
        except Exception:
            pass

        return {
            "session_id": session.session_id,
            "candidate_id": session.candidate_id,
            "job_id": session.job_id,
            "transcript": transcript,
            "status": session.status,
            "assessment": assessment,
            "created_at": session.created_at,
            "updated_at": session.updated_at
        }

    finally:
        db.close()
