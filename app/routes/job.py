import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from app.database import SessionLocal
from app.models.job import Job


router = APIRouter()


# -----------------------------------------
# Request Models
# -----------------------------------------

class JobSkill(BaseModel):
    name: str
    level: str = "Basic"


class JobCreate(BaseModel):
    title: str
    min_experience: int = 0
    skills: List[JobSkill]


# -----------------------------------------
# Create Job
# -----------------------------------------

@router.post("/jobs")
def create_job(job_data: JobCreate):

    db = SessionLocal()

    try:

        job = Job(
            title=job_data.title,
            min_experience=job_data.min_experience,
            skills=json.dumps(
                [skill.model_dump() for skill in job_data.skills]
            )
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        return {
            "message": "Job created successfully",
            "job_id": job.id,
            "job": {
                "id": job.id,
                "title": job.title,
                "min_experience": job.min_experience,
                "skills": json.loads(job.skills)
            }
        }

    finally:
        db.close()


# -----------------------------------------
# Get All Jobs
# -----------------------------------------

@router.get("/jobs")
def get_jobs():

    db = SessionLocal()

    try:

        jobs = (
            db.query(Job)
            .order_by(Job.created_at.desc())
            .all()
        )

        result = []

        for job in jobs:

            result.append({
                "id": job.id,
                "title": job.title,
                "min_experience": job.min_experience,
                "skills": json.loads(job.skills or "[]"),
                "created_at": job.created_at
            })

        return result

    finally:
        db.close()


# -----------------------------------------
# Get Single Job
# -----------------------------------------

@router.get("/job/{job_id}")
def get_job(job_id: int):

    db = SessionLocal()

    try:

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

        return {
            "id": job.id,
            "title": job.title,
            "min_experience": job.min_experience,
            "skills": json.loads(job.skills or "[]"),
            "created_at": job.created_at
        }

    finally:
        db.close()