import os
import shutil
import json
import json
from app.models.upload_history import UploadHistory
from fastapi import APIRouter, File, HTTPException, UploadFile
from app.services.parser import parse_resume
from app.services.extractor import extract_candidate_details
from datetime import datetime
from app.database import SessionLocal
from app.models.candidate import Candidate


router = APIRouter()

UPLOAD_FOLDER = "uploads"
EXTRACTED_FOLDER = "extracted_data"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXTRACTED_FOLDER, exist_ok=True)

from typing import List

@router.post("/upload")
async def upload_resume(files: List[UploadFile] = File(...)):

    db = SessionLocal()
    uploaded_candidates = []

    try:

        for file in files:

            # -------------------------
            # Validate File
            # -------------------------
            extension = os.path.splitext(file.filename)[1].lower()

            if extension not in [".pdf", ".docx"]:
                continue

            # -------------------------
            # Save Resume
            # -------------------------
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # -------------------------
            # Parse Resume
            # -------------------------
            raw_text = parse_resume(file_path)

            # -------------------------
            # Save TXT
            # -------------------------
            text_filename = os.path.splitext(file.filename)[0] + ".txt"
            text_path = os.path.join(EXTRACTED_FOLDER, text_filename)

            with open(text_path, "w", encoding="utf-8") as f:
                f.write(raw_text)

            # -------------------------
            # Extract Details
            # -------------------------
            candidate_data = extract_candidate_details(raw_text)

            # -------------------------
            # Save JSON
            # -------------------------
            json_filename = os.path.splitext(file.filename)[0] + ".json"
            json_path = os.path.join(EXTRACTED_FOLDER, json_filename)

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(candidate_data, f, indent=4)

            # -------------------------
            # Upload History
            # -------------------------
            db.add(UploadHistory())
            db.commit()

            email = candidate_data.get("email", "").strip().lower()

            existing = None

            if email:
                existing = (
                    db.query(Candidate)
                    .filter(Candidate.email == email)
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

                # ADD THIS LINE
                existing.uploaded_at = datetime.utcnow()

                db.commit()
                db.refresh(existing)

                uploaded_candidates.append(existing.id)

            else:

                candidate = Candidate(
                    name=candidate_data.get("name", ""),
                    email=email,
                    phone=candidate_data.get("phone", ""),
                    education=json.dumps(candidate_data.get("education", [])),
                    skills=json.dumps(candidate_data.get("skills", [])),
                    certifications=json.dumps(candidate_data.get("certifications", [])),
                    projects=json.dumps(candidate_data.get("projects", [])),
                    experience=json.dumps(candidate_data.get("experience", [])),
                    resume_path=file_path,
                    uploaded_at=datetime.utcnow()
                )

                db.add(candidate)
                db.commit()
                db.refresh(candidate)

                uploaded_candidates.append(candidate.id)

        return {
            "message": f"{len(uploaded_candidates)} resumes processed successfully",
            "candidate_ids": uploaded_candidates
        }

    finally:
        db.close()