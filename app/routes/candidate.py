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