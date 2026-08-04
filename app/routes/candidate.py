from fastapi import APIRouter, HTTPException
from app.database import SessionLocal
from app.models.candidate import Candidate
from sqlalchemy import func
from app.models.upload_history import UploadHistory

router = APIRouter()

@router.get("/candidates")
def get_all_candidates():

    db = SessionLocal()

    candidates = db.query(Candidate).all()

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

    candidates = db.query(Candidate).all()

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