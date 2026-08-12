from fastapi import APIRouter, HTTPException

from app.database import SessionLocal
from app.models.candidate import Candidate
from app.models.job import Job

from app.services.matching import (
    calculate_match,
    generate_skill_gap
)


router = APIRouter(
    prefix="/matching",
    tags=["Candidate Matching"]
)


# ============================================================
# GET ALL CANDIDATES MATCHED AGAINST A JOB
# ============================================================

@router.get("/job/{job_id}")
def match_candidates_for_job(job_id: int):

    db = SessionLocal()

    try:

        # -----------------------------------------
        # Find Job
        # -----------------------------------------

        job = (
            db.query(Job)
            .filter(Job.id == job_id)
            .first()
        )

        if not job:

            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )

        # -----------------------------------------
        # Get All Candidates
        # -----------------------------------------

        candidates = (
            db.query(Candidate)
            .order_by(Candidate.id.asc())
            .all()
        )

        results = []

        # -----------------------------------------
        # Calculate Match
        # -----------------------------------------

        for candidate in candidates:

            result = calculate_match(
                candidate,
                job
            )

            results.append(result)

        # -----------------------------------------
        # Highest Match First
        # -----------------------------------------

        results.sort(
            key=lambda x: x["match_score"],
            reverse=True
        )

        return results

    finally:

        db.close()


# ============================================================
# SKILL GAP ANALYSIS
# ============================================================

@router.get("/skill-gap/{job_id}/{candidate_id}")
def get_skill_gap(
    job_id: int,
    candidate_id: int
):

    db = SessionLocal()

    try:

        # -----------------------------------------
        # Find Job
        # -----------------------------------------

        job = (
            db.query(Job)
            .filter(Job.id == job_id)
            .first()
        )

        if not job:

            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )

        # -----------------------------------------
        # Find Candidate
        # -----------------------------------------

        candidate = (
            db.query(Candidate)
            .filter(
                Candidate.id == candidate_id
            )
            .first()
        )

        if not candidate:

            raise HTTPException(
                status_code=404,
                detail="Candidate not found"
            )

        # -----------------------------------------
        # Calculate Match
        # -----------------------------------------

        result = calculate_match(
            candidate,
            job
        )

        # -----------------------------------------
        # Generate Skill Gap
        # -----------------------------------------

        skill_gap = generate_skill_gap(
            result
        )

        return {

            "job_id": job.id,

            "job_title": job.title,

            "candidate_id":
                candidate.id,

            "candidate_name":
                candidate.name,

            "email":
                candidate.email,

            "match_score":
                result["match_score"],

            "match_level":
                result["match_level"],

            "matched_skills":
                result["matched_skills"],

            "missing_skills":
                result["missing_skills"],

            "candidate_experience":
                result[
                    "candidate_experience"
                ],

            "required_experience":
                result[
                    "required_experience"
                ],

            "skill_gap":
                skill_gap

        }

    finally:

        db.close()