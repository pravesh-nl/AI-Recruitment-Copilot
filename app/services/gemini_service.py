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
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )
    try:
        return response.choices[0].message.content
    except AttributeError:
        return response.text


def generate_job_interview_questions(
    job_title: str,
    min_experience: int,
    skills: list,
    question_type: str
):
    skills_str = ", ".join([f"{s.get('name', '')} ({s.get('level', 'Basic')})" for s in skills]) if skills else "None specified"
    
    prompt = f"""
You are an expert technical recruiter.

Generate exactly 5 interview questions for the following job:

Job Position: {job_title}
Minimum Experience Required: {min_experience} years
Required Skills: {skills_str}
Question Type: {question_type}

Requirements:

- Questions must be relevant to the job position, experience level, and required skills.
- Match the requested question type ({question_type}).
- Avoid generic questions.
- Make the questions realistic for an actual interview.
- Return ONLY the 5 questions, one per line. Do not number them or use bullet points, just the question text.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.7
    )

    try:
        return response.choices[0].message.content
    except AttributeError:
        # Fallback if the underlying object structure is different
        return response.text


def regenerate_job_interview_question(
    job_title: str,
    min_experience: int,
    skills: list,
    question_type: str,
    current_question: str
):
    skills_str = ", ".join([f"{s.get('name', '')} ({s.get('level', 'Basic')})" for s in skills]) if skills else "None specified"
    
    prompt = f"""
You are an expert technical recruiter.

We have the following interview question for a job:
"{current_question}"

Please generate ONE replacement interview question.

Job Position: {job_title}
Minimum Experience Required: {min_experience} years
Required Skills: {skills_str}
Question Type: {question_type}

Requirements:
- The new question must be different from the current question.
- It must remain relevant to the selected job, experience level, and required skills.
- It must match the requested question type ({question_type}).
- Avoid generic questions. Make it realistic for an actual interview.
- Return ONLY the ONE replacement question text. Do not number it or use bullet points. Do not include introductory or concluding remarks.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.8
    )

    try:
        return response.choices[0].message.content
    except AttributeError:
        return response.text


def start_interview_simulation(
    job_title: str,
    min_experience: int,
    job_skills: list,
    candidate_name: str,
    candidate_skills: str,
    candidate_experience: str,
    interview_mode: str
):
    skills_str = ", ".join([f"{s.get('name', '')} ({s.get('level', 'Basic')})" for s in job_skills]) if job_skills else "None specified"
    
    prompt = f"""
You are an expert AI technical recruiter conducting a live chat interview.

Context:
Job Position: {job_title}
Minimum Experience Required: {min_experience} years
Required Skills: {skills_str}

Candidate Profile:
Name: {candidate_name}
Skills: {candidate_skills}
Experience: {candidate_experience}

Interview Mode: {interview_mode}

Instructions:
You are to start the interview. Greet the candidate by name, briefly introduce yourself as the AI recruiter for this role, and ask the FIRST question.
The question should align with the {interview_mode} interview mode.
Do not provide multiple questions. Ask exactly one question and wait for the candidate's response.
Maintain a professional and conversational tone.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.7
    )

    try:
        return response.choices[0].message.content
    except AttributeError:
        return response.text


def generate_interview_response(conversation_history: list):
    # Prepare messages for Groq API
    # conversation_history is a list of dicts: {"role": "...", "content": "..."}
    # where roles can be 'system', 'assistant', 'user'
    messages = []
    
    # Prepend a system prompt to remind the AI of its role
    messages.append({
        "role": "system",
        "content": "You are an expert AI technical recruiter conducting a live chat interview. Ask ONE relevant follow-up question based on the candidate's response, or move on to the next topic if the answer was sufficient. Keep your responses concise and conversational."
    })
    
    for msg in conversation_history:
        # map our internal roles to groq roles if needed, but they should align
        messages.append({
            "role": msg.get("role", "user"),
            "content": msg.get("content", "")
        })

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        temperature=0.7
    )

    try:
        return response.choices[0].message.content
    except AttributeError:
        return response.text


def generate_interview_summary(conversation_history: list, job_title: str = "", job_skills: list = None):
    skills_str = ", ".join([f"{s.get('name', '')}" for s in job_skills]) if job_skills else "None specified"
    
    system_prompt = f"""
You are an expert technical recruiter evaluating a candidate's performance in an interview for the {job_title} role.
The candidate was evaluated based on the following required skills: {skills_str}.

Analyze the preceding interview conversation and provide a structured JSON evaluation.

You MUST respond with valid JSON matching exactly this structure:
{{
  "overall_score": <float between 0 and 10>,
  "skill_ratings": [
    {{
      "skill": "<skill_name>",
      "score": <float between 0 and 10>,
      "reason": "<short justification based on the interview>"
    }}
  ],
  "strengths": [
    "<strength 1>",
    "<strength 2>"
  ],
  "areas_for_improvement": [
    "<area 1>",
    "<area 2>"
  ],
  "overall_feedback": "<brief recruiter-friendly summary>"
}}

Do NOT include markdown block backticks (```json). Just return the JSON object directly. Ensure it is perfectly parseable.
"""

    messages = []
    for msg in conversation_history:
        messages.append({
            "role": msg.get("role", "user"),
            "content": msg.get("content", "")
        })
        
    messages.append({
        "role": "user",
        "content": system_prompt
    })

    # Note: Groq supports response_format={"type": "json_object"} on some models.
    # To be safe across models (like openai/gpt-oss-120b or groq equivalents), 
    # we explicitly ask for JSON in the prompt and use the parameter if available.
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        temperature=0.3,
        response_format={"type": "json_object"}
    )

    try:
        return response.choices[0].message.content
    except AttributeError:
        return response.text