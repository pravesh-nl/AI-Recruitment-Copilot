import os
import shutil
import json
import json
from app.models.upload_history import UploadHistory
from fastapi import APIRouter, File, HTTPException, UploadFile
from app.services.parser import parse_resume
from app.services.extractor import extract_candidate_details

from app.database import SessionLocal
from app.models.candidate import Candidate

router = APIRouter()

UPLOAD_FOLDER = "uploads"
EXTRACTED_FOLDER = "extracted_data"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXTRACTED_FOLDER, exist_ok=True)


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):

    allowed_extensions = [".pdf", ".docx"]

    extension = os.path.splitext(file.filename)[1].lower()

    if extension not in [".pdf", ".docx"]:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are allowed."
        )

    # Save resume
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Parse resume
    raw_text = parse_resume(file_path)

    # Save raw text
    text_filename = os.path.splitext(file.filename)[0] + ".txt"
    text_path = os.path.join(EXTRACTED_FOLDER, text_filename)

    with open(text_path, "w", encoding="utf-8") as f:
        f.write(raw_text)

    # Extract structured information
    candidate_data = extract_candidate_details(raw_text)

    # Save JSON
    json_filename = os.path.splitext(file.filename)[0] + ".json"
    json_path = os.path.join(EXTRACTED_FOLDER, json_filename)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(candidate_data, f, indent=4)

    # Store in SQLite
    db = SessionLocal()

# Count every upload
    db.add(UploadHistory())
    db.commit()

# Check if candidate already exists
    existing = None

    if candidate_data.get("email"):
        existing = (
        db.query(Candidate)
        .filter(Candidate.email == candidate_data["email"])
        .first()
    )

    if existing:

        existing.name = candidate_data.get("name", "")
        existing.phone = candidate_data.get("phone", "")
        existing.education = json.dumps(candidate_data.get("education", []))
        existing.skills = json.dumps(candidate_data.get("skills", []))
        existing.certifications = json.dumps(candidate_data.get("certifications", []))
        existing.projects = json.dumps(candidate_data.get("projects", []))
        existing.experience = json.dumps(candidate_data.get("experience", []))
        existing.resume_path = file_path

        db.commit()
        db.refresh(existing)

        candidate = existing

    else:

        candidate = Candidate(
            name=candidate_data.get("name", ""),
            email=candidate_data.get("email", ""),
            phone=candidate_data.get("phone", ""),
            education=json.dumps(candidate_data.get("education", [])),
            skills=json.dumps(candidate_data.get("skills", [])),
            certifications=json.dumps(candidate_data.get("certifications", [])),
            projects=json.dumps(candidate_data.get("projects", [])),
            experience=json.dumps(candidate_data.get("experience", [])),
            resume_path=file_path
    )

    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    db.close()

    return {
        "message": "Resume uploaded successfully",
        "candidate_id": candidate.id,
        "candidate": candidate_data
    }