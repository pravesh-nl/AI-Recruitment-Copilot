import json
import os
import time
from google.genai import errors
from dotenv import load_dotenv
from groq import Groq

load_dotenv()


client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)
""""
def call_gemini_with_retry(prompt):

    max_retries = 3

    for attempt in range(max_retries):

        try:
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

            return response


        except Exception as e:

            error = str(e)

            if "429" in error or "RESOURCE_EXHAUSTED" in error:

                wait_time = 2 ** attempt

                print(
                    f"Gemini rate limit hit. Waiting {wait_time}s..."
                )

                time.sleep(wait_time)

            else:
                raise e


    raise Exception(
        "Gemini failed after multiple retries"
 )"""
    
def analyze_all_skills(required_skills, candidate_data):
    """
    Analyze all required skills for a candidate
    using a single Gemini API request.
    """

    skills_text = "\n".join(
        f"- {skill}"
        for skill in required_skills
    )

    prompt = f"""
You are an expert technical recruiter.

Analyze the candidate's resume evidence against ALL required skills.

REQUIRED SKILLS:
{skills_text}

CANDIDATE DATA:
{json.dumps(candidate_data, indent=2)}

For EACH required skill, determine:

1. status:
   - "explicit"
   - "inferred"
   - "missing"

2. level:
   - "Basic"
   - "Intermediate"
   - "Expert"
   - null if missing

3. confidence:
   A number between 0 and 1.

4. evidence:
   Briefly explain the resume evidence supporting your decision.

Level rules:
- Basic = limited exposure, basic usage, coursework, simple project usage.
- Intermediate = meaningful project work, multiple uses, practical implementation.
- Expert = extensive professional/project experience, advanced implementation, leadership, or deep demonstrated expertise.
- For inferred skills, be conservative. Do NOT assign Expert unless the resume provides very strong evidence.
- Missing skills must have level = null.
- Do NOT determine level only from the status. Use the actual resume evidence.

- Do NOT assume a skill merely because it is vaguely related.
- Reasonable technical inference is allowed.
- For example, if a candidate built a responsive web application,
  CSS may reasonably be inferred even if CSS is not explicitly listed.
- Do not infer a skill when the evidence is weak or unrelated.
- Do not treat an explicitly listed skill as automatically Advanced.
- Do not invent experience that is not present in the resume.

Return ONLY valid JSON in this format:
Return ONLY a JSON array.

Example:

{
 {
  "skill": "Python",
  "status": "explicit",
  "level": "Intermediate",
  "confidence": 1.0,
  "evidence": "Python is listed and used in projects."
 }
}
"""

    # ========================================================
    # GEMINI API CALL
    # ========================================================

    try:
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
    except Exception as e:

        print(
            f"\n[WARNING] Gemini skill analysis unavailable: {e}\n"
        )

        # Safe fallback
        return [
            {
                "skill": skill,
                "status": "missing",
                "level": None,
                "confidence": 0.0,
                "evidence": (
                    "Gemini analysis unavailable. "
                    "No AI-based evidence analysis was performed."
                )
            }
            for skill in required_skills
        ]

    # ========================================================
    # PARSE GEMINI RESPONSE
    # ========================================================

    try:

        text = response.choices[0].message.content

        # Remove markdown code fences if Gemini adds them
        if text.startswith("```"):

            text = text.replace(
                "```json",
                ""
            )

            text = text.replace(
                "```",
                ""
            )

            text = text.strip()

            data = json.loads(text)

            # If model returns direct list
            if isinstance(data, list):
                return data

            # If model returns {"skills": [...]}
            elif isinstance(data, dict):
                return data.get("skills", [])

            else:
                return []
    except Exception as e:

        print(
            f"\n[WARNING] Failed to parse Gemini response: {e}\n"
        )

        return [
            {
                "skill": skill,
                "status": "missing",
                "level": None,
                "confidence": 0.0,
                "evidence": (
                    "Gemini returned an invalid response. "
                    "No AI-based evidence analysis was performed."
                )
            }
            for skill in required_skills
        ]



# ------------------------------------------------------------
# Gemini request with retry
# ------------------------------------------------------------

    for attempt in range(3):

        try:

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
            break

        except errors.ServerError as e:

            if attempt == 2:
                raise

            time.sleep(2 * (attempt + 1))

    text = response.choices[0].message.content

    # Remove markdown code fences if Gemini adds them
    if text.startswith("```"):
        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

    return json.loads(text)