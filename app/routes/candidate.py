from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import SessionLocal
from app.models.candidate import Candidate
from sqlalchemy import func
from app.models.upload_history import UploadHistory

router = APIRouter()

@router.get("/candidates")
def get_all_candidates():

    db = SessionLocal()

    candidates = (
    db.query(Candidate)
    .order_by(Candidate.uploaded_at.desc())
    .all()
)

    db.close()

    return candidates


@router.get("/candidate/{candidate_id}")
def get_candidate(candidate_id: int):

    db = SessionLocal()

    candidate = (
        db.query(Candidate)
        .filter(Candidate.id == candidate_id)
        .first()
    )

    db.close()

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found"
        )

    return candidate


@router.get("/candidate/{candidate_id}/evaluations")
def get_candidate_evaluations(candidate_id: int, job_id: int = None):
    """
    Retrieve the latest AI Interview and Voice Screening evaluations for a candidate.
    If job_id is provided, return job-specific evaluations.
    """
    import json
    from app.models.interview_session import InterviewSession
    from app.models.voice_screening_session import VoiceScreeningSession
    from app.services.voice_screening_service import derive_screening_decision

    db = SessionLocal()
    try:
        # Get latest completed interview session
        interview_query = db.query(InterviewSession).filter(
            InterviewSession.candidate_id == candidate_id,
            InterviewSession.status == "completed"
        )
        if job_id:
            interview_query = interview_query.filter(InterviewSession.job_id == job_id)
            
        interview = interview_query.order_by(InterviewSession.created_at.desc()).first()

        ai_eval = {
            "score": "N/A",
            "recommendation": "Pending / Not Evaluated",
            "feedback": "",
            "interview_status": "Interview Done" if interview else "Interview Not Done"
        }
        
        if interview and interview.feedback:
            try:
                fb = json.loads(interview.feedback)
                ai_eval["score"] = fb.get("overall_score", "N/A")
                ai_eval["recommendation"] = fb.get("recommendation", "Pending / Not Evaluated")
                
                # Check for other recommendation fields if 'recommendation' is missing
                if ai_eval["recommendation"] == "Pending / Not Evaluated":
                    if "overall_score" in fb and fb["overall_score"] != "N/A":
                        score = float(fb["overall_score"])
                        ai_eval["recommendation"] = "Recommended" if score >= 6.0 else "Not Recommended"
                
                ai_eval["feedback"] = fb.get("overall_feedback", "")
            except Exception as e:
                print(f"Error parsing AI feedback: {e}")

        # Get latest completed voice screening session
        voice_query = db.query(VoiceScreeningSession).filter(
            VoiceScreeningSession.candidate_id == candidate_id,
            VoiceScreeningSession.status == "completed"
        )
        if job_id:
            voice_query = voice_query.filter(VoiceScreeningSession.job_id == job_id)
            
        voice = voice_query.order_by(VoiceScreeningSession.created_at.desc()).first()

        voice_eval = {
            "overall_score": "N/A",
            "communication_score": "N/A",
            "status": "Pending", # Retaining existing Screened/Not Screened terminology
            "feedback": ""
        }
        
        if voice and voice.assessment:
            try:
                assessment = json.loads(voice.assessment)
                voice_eval["overall_score"] = assessment.get("overall_score", "N/A")
                voice_eval["communication_score"] = assessment.get("communication_score", "N/A")
                
                # Retrieve existing status or derive it if missing
                status = assessment.get("status")
                if not status:
                    from app.services.voice_screening_service import derive_screening_decision
                    status = derive_screening_decision(assessment)
                voice_eval["status"] = status
                
                voice_eval["feedback"] = assessment.get("overall_feedback", "")
            except Exception as e:
                print(f"Error parsing Voice assessment: {e}")

        # ATS Match evaluation (backward compatible addition)
        ats_eval = None
        eval_job_id = job_id
        if not eval_job_id:
            if interview:
                eval_job_id = interview.job_id
            elif voice:
                eval_job_id = voice.job_id
            
        if not eval_job_id:
            from app.models.job import Job
            latest_job = db.query(Job).order_by(Job.id.desc()).first()
            if latest_job:
                eval_job_id = latest_job.id

        if eval_job_id:
            from app.models.job import Job
            from app.services.matching import calculate_match, generate_skill_gap
            job = db.query(Job).filter(Job.id == eval_job_id).first()
            c = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            if job and c:
                try:
                    res = calculate_match(c, job)
                    sg = generate_skill_gap(res)
                    ats_eval = {
                        "score": res.get("match_score", "N/A"),
                        "tier": res.get("match_level", "Unknown"),
                        "skill_gap": sg
                    }
                except Exception as e:
                    print(f"Error calculating ATS match for evaluations: {e}")

        return {
            "ats_match": ats_eval,
            "ai_interview": ai_eval,
            "voice_screening": voice_eval
        }
    finally:
        db.close()
@router.get("/stats")
def get_stats():

    db = SessionLocal()

    resume_processed = db.query(func.count(UploadHistory.id)).scalar()

    profiles_created = db.query(func.count(Candidate.id)).scalar()

    candidates = (
    db.query(Candidate)
    .order_by(Candidate.id.desc())
    .all()
)

    db.close()

    if profiles_created == 0:
        return {
            "resume_processed": 0,
            "profiles_created": 0,
            "parsing_accuracy": 0
        }

    total_accuracy = 0


    for c in candidates:

     
        score = 0

        if c.name:
            score += 20

        if c.email:
            score += 20

        if c.phone:
            score += 10

        if c.skills:
            score += 20

        if c.education:
            score += 15

        if c.experience:
            score += 10

        if c.projects:
            score += 3

        if c.certifications:
            score += 2

        total_accuracy += score

        

    avg_accuracy = round(total_accuracy / profiles_created)

    return {
        "resume_processed": resume_processed,
        "profiles_created": profiles_created,
        "parsing_accuracy": avg_accuracy
    }


# ==============================================================
# Milestone 4: PATCH /candidates/{candidate_id}/stage
# Allows recruiter to manually update a candidate's pipeline stage.
# ==============================================================

VALID_STAGES = ["applied", "screened", "interviewed", "offered", "hired"]


class StageUpdate(BaseModel):
    stage: str


@router.patch("/candidates/{candidate_id}/stage")
def update_candidate_stage(candidate_id: int, body: StageUpdate):
    """
    Update the recruitment pipeline stage for a candidate.
    The recruiter is responsible for all stage decisions.
    AI recommendations do NOT automatically trigger this endpoint.
    """
    if body.stage not in VALID_STAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid stage '{body.stage}'. Must be one of: {VALID_STAGES}"
        )

    db = SessionLocal()
    try:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        candidate.recruitment_stage = body.stage
        db.commit()

        return {
            "message": f"Stage updated to '{body.stage}'",
            "candidate_id": candidate_id,
            "stage": body.stage
        }
    finally:
        db.close()


# ==============================================================
# Recruiter Hiring Decision: PATCH /candidates/{candidate_id}/hiring-status
# ==============================================================

VALID_HIRING_STATUSES = ["IN_PROGRESS", "HIRED", "NOT_SELECTED", "NOT_EVALUATED"]

class HiringStatusUpdate(BaseModel):
    status: str

@router.patch("/candidates/{candidate_id}/hiring-status")
def update_hiring_status(candidate_id: int, body: HiringStatusUpdate):
    """
    Update the recruiter's explicit hiring decision for a candidate.
    Must not be automated.
    """
    if body.status not in VALID_HIRING_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{body.status}'. Must be one of: {VALID_HIRING_STATUSES}"
        )

    db = SessionLocal()
    try:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        candidate.hiring_status = body.status
        db.commit()

        return {
            "message": f"Hiring status updated to '{body.status}'",
            "candidate_id": candidate_id,
            "hiring_status": body.status
        }
    finally:
        db.close()