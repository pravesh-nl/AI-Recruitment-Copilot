import os
from app.services.gemini_service import generate_interview_questions

result = generate_interview_questions(
    "Backend Developer",
    "Technical Skills"
)

print(result)