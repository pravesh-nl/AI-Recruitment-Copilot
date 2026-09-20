import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import SessionLocal
from app.models.job import Job
from app.services.gemini_service import generate_job_interview_questions


router = APIRouter(
    prefix="/interview",
    tags=["Interview"]
)


class InterviewQuestionRequest(BaseModel):
    job_id: int
    question_type: str


SUPPORTED_QUESTION_TYPES = [
    "technical", 
    "behavioral", 
    "scenario-based", 
    "experience-based", 
    "hr"
]


@router.post("/generate-questions")
def generate_questions(request: InterviewQuestionRequest):

    if request.question_type not in SUPPORTED_QUESTION_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported question type. Must be one of: {', '.join(SUPPORTED_QUESTION_TYPES)}"
        )

    db = SessionLocal()
    try:

        job = db.query(Job).filter(Job.id == request.job_id).first()

        if not job:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )

        skills = json.loads(job.skills or "[]")

        try:
            questions_text = generate_job_interview_questions(
                job_title=job.title,
                min_experience=job.min_experience,
                skills=skills,
                question_type=request.question_type
            )

            # Convert Groq text into a list
            questions = [
                line.strip().lstrip("1234567890.- ")
                for line in questions_text.split("\n")
                if line.strip()
            ]

            # Ensure exactly 5 questions
            if len(questions) > 5:
                questions = questions[:5]
            elif len(questions) == 0:
                raise ValueError("LLM returned an empty response")

            return {
                "job_id": job.id,
                "job_title": job.title,
                "question_type": request.question_type,
                "questions": questions
            }

        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=str(e)
            )

    finally:
        db.close()


class RegenerateQuestionRequest(BaseModel):
    job_id: int
    question_type: str
    question: str


@router.post("/regenerate-question")
def regenerate_question(request: RegenerateQuestionRequest):
    if request.question_type not in SUPPORTED_QUESTION_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported question type. Must be one of: {', '.join(SUPPORTED_QUESTION_TYPES)}"
        )

    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == request.job_id).first()

        if not job:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )

        skills = json.loads(job.skills or "[]")

        try:
            # We import it here or at the top of the file
            from app.services.gemini_service import regenerate_job_interview_question
            
            new_question_text = regenerate_job_interview_question(
                job_title=job.title,
                min_experience=job.min_experience,
                skills=skills,
                question_type=request.question_type,
                current_question=request.question
            )

            # Clean up the output string
            new_question = new_question_text.strip().lstrip("1234567890.- ")
            
            if not new_question:
                raise ValueError("LLM returned an empty response")

            return {
                "question": new_question,
                "regeneration_count": 1
            }

        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=str(e)
            )

    finally:
        db.close()


import uuid
from app.models.candidate import Candidate
from app.models.interview_session import InterviewSession
from app.services.gemini_service import (
    start_interview_simulation,
    generate_interview_response,
    generate_interview_summary
)


class InterviewStartRequest(BaseModel):
    candidate_id: int
    job_id: int
    interview_mode: str


class InterviewMessageRequest(BaseModel):
    message: str


@router.post("/start")
def start_interview(request: InterviewStartRequest):
    allowed_modes = ["technical", "behavioral", "mixed"]
    if request.interview_mode not in allowed_modes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid interview mode. Must be one of {allowed_modes}"
        )

    db = SessionLocal()
    try:
        candidate = db.query(Candidate).filter(Candidate.id == request.candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        job = db.query(Job).filter(Job.id == request.job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        job_skills = json.loads(job.skills or "[]")
        
        try:
            initial_message = start_interview_simulation(
                job_title=job.title,
                min_experience=job.min_experience,
                job_skills=job_skills,
                candidate_name=candidate.name or "Candidate",
                candidate_skills=candidate.skills or "Not specified",
                candidate_experience=candidate.experience or "Not specified",
                interview_mode=request.interview_mode
            )

            session_id = str(uuid.uuid4())
            conversation_history = [
                {"role": "assistant", "content": initial_message}
            ]

            session = InterviewSession(
                session_id=session_id,
                candidate_id=candidate.id,
                job_id=job.id,
                interview_mode=request.interview_mode,
                conversation_history=json.dumps(conversation_history),
                status="active"
            )

            db.add(session)
            db.commit()

            # Milestone 4: auto-advance stage to 'interviewed' if at an earlier stage.
            # NEVER overwrites offered/hired — recruiter decisions are preserved.
            try:
                if candidate.recruitment_stage in (None, "applied", "screened"):
                    candidate.recruitment_stage = "interviewed"
                    db.commit()
            except Exception:
                pass  # Stage update failure must not block the interview start response

            return {
                "session_id": session_id,
                "initial_message": initial_message
            }

        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=str(e)
            )

    finally:
        db.close()


@router.post("/{session_id}/message")
def send_interview_message(session_id: str, request: InterviewMessageRequest):
    db = SessionLocal()
    try:
        session = db.query(InterviewSession).filter(InterviewSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Interview session not found")
        
        if session.status != "active":
            raise HTTPException(status_code=400, detail="Interview session is already completed")

        conversation_history = json.loads(session.conversation_history)
        
        # Count AI messages to determine the current question number
        assistant_count = sum(1 for msg in conversation_history if msg["role"] == "assistant")
        
        # Append user message
        conversation_history.append({"role": "user", "content": request.message})

        if assistant_count >= 7:
            # Reached limit! Do NOT generate an 8th question.
            session.conversation_history = json.dumps(conversation_history)
            db.commit()
            return {
                "ai_response": "Thank you. The interview is now complete.",
                "interview_completed": True
            }

        try:
            ai_response = generate_interview_response(conversation_history)

            # Append AI response
            conversation_history.append({"role": "assistant", "content": ai_response})

            # Update DB
            session.conversation_history = json.dumps(conversation_history)
            db.commit()

            return {
                "ai_response": ai_response,
                "interview_completed": False
            }
        
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    finally:
        db.close()


@router.post("/{session_id}/end")
def end_interview(session_id: str):
    import logging
    logger = logging.getLogger("interview.end")

    db = SessionLocal()
    try:
        session = db.query(InterviewSession).filter(InterviewSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Interview session not found")

        # ── IDEMPOTENCY: already completed → return existing summary ──────────
        # This handles the case where sendSimMessage auto-triggers endInterviewBtn
        # after the 7th question AND the user has already clicked End once.
        # Raising 400 here would cause the frontend to swallow the summary silently.
        if session.status == "completed":
            existing_summary = {}
            if session.feedback:
                try:
                    existing_summary = json.loads(session.feedback)
                except Exception:
                    pass
            return {
                "message": "Interview already completed",
                "summary": existing_summary,
                "session_id": session_id
            }

        conversation_history = json.loads(session.conversation_history)

        job = db.query(Job).filter(Job.id == session.job_id).first()
        job_title = job.title if job else ""
        job_skills = json.loads(job.skills or "[]") if job else []

        # ── DETERMINISTIC ANSWER COUNT (Python, not LLM) ─────────────────────
        from app.services.gemini_service import _count_meaningful_answers
        meaningful_count = _count_meaningful_answers(conversation_history)
        total_q = 7

        # ── ZERO-ANSWER GUARD ─────────────────────────────────────────────────
        # If the candidate provided zero meaningful answers, skip the LLM call
        # and persist a safe "Not Recommended" result immediately.
        # This prevents the LLM from ever awarding a positive result on an empty session.
        if meaningful_count == 0:
            summary = {
                "overall_score": 0.0,
                "recommendation": "Not Recommended",
                "skill_ratings": [],
                "strengths": [],
                "areas_for_improvement": ["Communication", "Engagement"],
                "overall_feedback": (
                    "The candidate did not provide any meaningful answers during the interview. "
                    "Insufficient evidence to evaluate."
                ),
                "questions_answered": 0,
                "total_questions": total_q
            }
            session.status = "completed"
            session.feedback = json.dumps(summary)
            db.commit()
            logger.info(
                "Interview %s ended with 0 meaningful answers → Not Recommended (no LLM call).",
                session_id
            )
            return {"message": "Interview ended successfully", "summary": summary}

        try:
            summary_json_str = generate_interview_summary(conversation_history, job_title, job_skills)

            # ── Parse LLM result ─────────────────────────────────────────────
            try:
                summary = json.loads(summary_json_str)
            except (json.JSONDecodeError, TypeError, ValueError):
                # LLM returned malformed JSON — safe fallback, saved to DB as Pending
                logger.warning("Interview %s: LLM returned unparseable JSON. Saving fallback.", session_id)
                summary = {
                    "overall_score": 0.0,
                    "recommendation": "Not Recommended",
                    "skill_ratings": [],
                    "strengths": [],
                    "areas_for_improvement": [],
                    "overall_feedback": "Evaluation could not be completed — AI response was malformed. Please retry.",
                    "questions_answered": meaningful_count,
                    "total_questions": total_q
                }

            # ── DETERMINISTIC RECOMMENDATION (override LLM) ───────────────────
            # Always derive recommendation from score, never trust raw LLM text.
            # This prevents arbitrary/hallucinated recommendation strings.
            score = summary.get("overall_score", 0)
            try:
                score = float(score)
            except (TypeError, ValueError):
                score = 0.0
                summary["overall_score"] = 0.0

            # Enforce: 0 meaningful answers → always Not Recommended
            if meaningful_count == 0:
                summary["recommendation"] = "Not Recommended"
            elif score >= 6.0:
                summary["recommendation"] = "Recommended"
            else:
                summary["recommendation"] = "Not Recommended"

            # Always stamp the Python-counted values (not LLM-reported)
            summary["questions_answered"] = meaningful_count
            summary["total_questions"] = total_q

            # ── Persist ───────────────────────────────────────────────────────
            session.status = "completed"
            session.feedback = json.dumps(summary)
            db.commit()
            logger.info(
                "Interview %s ended. meaningful_count=%d, score=%.1f, recommendation=%s",
                session_id, meaningful_count, score, summary["recommendation"]
            )

            return {"message": "Interview ended successfully", "summary": summary}

        except Exception as e:
            logger.error("Interview %s end error: %s", session_id, str(e))
            raise HTTPException(status_code=503, detail=str(e))

    finally:
        db.close()

# ============================================================
# ATS INTEGRATION
# ============================================================

@router.get("/ats-status")
def get_ats_candidates():
    db = SessionLocal()
    try:
        candidates = db.query(Candidate).all()
        jobs = db.query(Job).all()

        results = []
        for candidate in candidates:
            for job in jobs:
                # --------------------------------------------------------
                # Step 1: Determine interview status from DB only.
                # No LLM, no matching service involved here.
                # --------------------------------------------------------
                session = db.query(InterviewSession).filter(
                    InterviewSession.candidate_id == candidate.id,
                    InterviewSession.job_id == job.id
                ).order_by(InterviewSession.created_at.desc()).first()

                interview_status = "Not scheduled"
                session_id = None
                if session:
                    session_id = session.session_id
                    if session.status == "active":
                        interview_status = "Interview in progress"
                    elif session.status == "completed":
                        interview_status = "Completed"

                # --------------------------------------------------------
                # Milestone 4 fix: ATS status is DB-only.
                # calculate_match() is NOT called here because it invokes
                # the Groq/Gemini AI which can fail with 429 rate-limit errors.
                # ATS must always return 200 regardless of AI availability.
                # --------------------------------------------------------
                match_percentage = None  # Not calculated here — use /matching/job/{id} for scores

                results.append({
                    "candidate_id": candidate.id,
                    "candidate_name": candidate.name or "Unknown",
                    "job_id": job.id,
                    "job_title": job.title,
                    "match_percentage": match_percentage,
                    "status": interview_status,
                    "session_id": session_id
                })

        return {"candidates": results}
    finally:
        db.close()