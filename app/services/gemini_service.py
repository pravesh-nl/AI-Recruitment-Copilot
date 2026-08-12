import os
from dotenv import load_dotenv
from groq import Groq
import time
load_dotenv(override=True)



client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def generate_interview_questions(
    job_title: str,
    question_type: str
):
    prompt = f"""
You are an expert technical recruiter.

Generate exactly 5 interview questions for the following job:

Job Position: {job_title}
Question Type: {question_type}

Requirements:

- Questions must be relevant to the job position.
- Match the requested question type.
- Avoid generic questions.
- Make the questions realistic for an actual interview.
- Number the questions from 1 to 5.
- Return ONLY the questions.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    return response.text