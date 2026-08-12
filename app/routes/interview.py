from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.gemini_service import generate_interview_questions


router = APIRouter(
    prefix="/interview",
    tags=["Interview"]
)


class InterviewQuestionRequest(BaseModel):
    job_title: str
    question_type: str


@router.post("/generate-questions")
def generate_questions(request: InterviewQuestionRequest):

    try:

        questions_text = generate_interview_questions(
            request.job_title,
            request.question_type
        )

        # Convert Gemini text into a list
        questions = [
            line.strip()
            for line in questions_text.split("\n")
            if line.strip()
        ]

        return {
            "success": True,
            "job_title": request.job_title,
            "question_type": request.question_type,
            "questions": questions
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )