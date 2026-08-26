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
                status_code=500,
                detail=f"Failed to generate questions: {str(e)}"
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
                status_code=500,
                detail=f"Failed to regenerate question: {str(e)}"
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

            return {
                "session_id": session_id,
                "initial_message": initial_message
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to start interview: {str(e)}"
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
        
        # Append user message
        conversation_history.append({"role": "user", "content": request.message})

        try:
            ai_response = generate_interview_response(conversation_history)

            # Append AI response
            conversation_history.append({"role": "assistant", "content": ai_response})

            # Update DB
            session.conversation_history = json.dumps(conversation_history)
            db.commit()

            return {
                "ai_response": ai_response
            }
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")

    finally:
        db.close()


@router.post("/{session_id}/end")
def end_interview(session_id: str):
    db = SessionLocal()
    try:
        session = db.query(InterviewSession).filter(InterviewSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Interview session not found")

        if session.status == "completed":
            raise HTTPException(status_code=400, detail="Interview session is already completed")

        conversation_history = json.loads(session.conversation_history)
        
        job = db.query(Job).filter(Job.id == session.job_id).first()
        job_title = job.title if job else ""
        job_skills = json.loads(job.skills or "[]") if job else []

        try:
            summary_json_str = generate_interview_summary(conversation_history, job_title, job_skills)
            
            try:
                summary = json.loads(summary_json_str)
            except json.JSONDecodeError:
                # Fallback if the LLM didn't return perfectly parseable JSON
                summary = {
                    "overall_score": 0,
                    "skill_ratings": [],
                    "strengths": [],
                    "areas_for_improvement": [],
                    "overall_feedback": summary_json_str
                }

            # Update DB
            session.status = "completed"
            session.feedback = json.dumps(summary)
            db.commit()

            return {
                "message": "Interview ended successfully",
                "summary": summary
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")

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
                # Step 2: Attempt to get the match percentage.
                # If the matching service or Groq/Gemini is unavailable
                # (e.g. 429 rate limit), fall back to 0 gracefully.
                # ATS status is NEVER blocked by this failure.
                # --------------------------------------------------------
                match_percentage = 0
                try:
                    from app.services.matching import calculate_match
                    match_result = calculate_match(candidate, job)
                    match_percentage = match_result.get("match_score", 0)
                except Exception as match_err:
                    print(
                        f"[WARNING] ATS match score unavailable for "
                        f"candidate={candidate.id} job={job.id}: {match_err}"
                    )

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