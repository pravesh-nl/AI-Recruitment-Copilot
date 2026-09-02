"""
Voice Screening Service — Milestone 4
Reuses the existing Groq client pattern from gemini_service.py.
Does NOT introduce a new AI provider.
Handles 429 rate-limit errors gracefully without crashing.

IMPORTANT — Role of this service:
  This is a PRELIMINARY VOICE SCREENING service, NOT a full technical interview.
  It evaluates: communication, fluency, confidence, professionalism,
  basic leadership/teamwork indicators, and basic domain familiarity.
  The AI Interview Assistant handles deep technical/behavioral evaluation separately.

Screened / Not Screened threshold (deterministic — NOT LLM-decided):
  SCREENED     = communication_score >= 5.5 AND overall_score >= 5.0
  NOT SCREENED = communication_score <  5.5 OR  overall_score <  5.0

Answer Naturalness indicator:
  Added as two additional fields inside the existing assessment JSON:
    answer_naturalness   : "Natural" | "Possibly Scripted" | "Highly Scripted / Potentially AI-Assisted" | "Unable to Analyze"
    naturalness_feedback : short observation string
  These fields are informational ONLY — they do NOT affect Screened / Not Screened.
  IMPORTANT: This is NOT an AI detector. It uses cautious observational language.
"""

import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv(override=True)

# Reuse the same Groq client pattern as gemini_service.py
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "openai/gpt-oss-120b"


def _is_rate_limit_error(error_str: str) -> bool:
    return "429" in error_str or "rate_limit" in error_str.lower() or "RESOURCE_EXHAUSTED" in error_str


def _is_llm_unavailable_error(error_str: str) -> bool:
    """Returns True for any error that indicates the LLM is unreachable or unavailable."""
    lower = error_str.lower()
    return (
        "429" in error_str
        or "rate_limit" in lower
        or "resource_exhausted" in lower
        or "503" in error_str
        or "502" in error_str
        or "connection" in lower
        or "timeout" in lower
        or "timed out" in lower
        or "invalid api key" in lower
        or "authentication" in lower
        or "unauthorized" in lower
    )


def derive_screening_decision(assessment: dict) -> str:
    """
    Deterministically derive a screening decision from the existing assessment scores.
    This function is the single source of truth for Screened / Not Screened status.

    Threshold (documented):
      SCREENED     = communication_score >= 5.5 AND overall_score >= 5.0
      NOT SCREENED = communication_score <  5.5 OR  overall_score <  5.0

    Returns "Screened" or "Not Screened".
    """
    if not assessment:
        return "Not Screened"
    comm = float(assessment.get("communication_score") or 0)
    overall = float(assessment.get("overall_score") or 0)
    if comm >= 5.5 and overall >= 5.0:
        return "Screened"
    return "Not Screened"


def generate_screening_question(
    job_title: str,
    job_skills: list,
    candidate_name: str,
    candidate_skills: str,
    conversation_history: list
) -> str:
    """
    Generate the next PRELIMINARY voice screening question from NovaAI.
    Focuses on communication, professional tone, and basic role familiarity — NOT deep technical topics.
    conversation_history is a list of {role: "ai"|"candidate", content: "..."} dicts.
    Returns the question string.
    Raises Exception with a user-friendly message on failure.
    """
    skills_str = ", ".join(
        [s.get("name", "") for s in job_skills if s.get("name")]
    ) if job_skills else "Not specified"

    is_first = len(conversation_history) == 0

    if is_first:
        prompt = (
            f"You are NovaAI, conducting a PRELIMINARY VOICE SCREENING (not a full interview) for the {job_title} position.\n\n"
            f"Candidate Name: {candidate_name}\n"
            f"Job Position: {job_title}\n"
            f"Role Context: {skills_str}\n"
            f"Candidate Background: {candidate_skills}\n\n"
            "Screening Purpose: This is an INITIAL PRELIMINARY SCREENING to assess spoken communication, "
            "professional tone, and basic fit — NOT a technical interview.\n\n"
            f"Instructions:\n"
            f"1. Greet the candidate warmly by name and briefly introduce yourself as NovaAI "
            f"(e.g., 'Hello {candidate_name}, I am NovaAI, your preliminary voice screening assistant.').\n"
            "2. Ask ONE clear opening question focused on: professional background, "
            "what motivates them, communication style, or teamwork/collaboration approach. "
            "Do NOT ask deep technical or coding questions.\n"
            "3. Keep your entire spoken response under 3 sentences.\n"
            "4. Return ONLY the spoken text — no stage directions, no bullet points, no markdown formatting."
        )
    else:
        history_lines = []
        for turn in conversation_history:
            role = turn.get("role", "")
            content = turn.get("content", "")
            if role == "ai":
                history_lines.append(f"NovaAI: {content}")
            elif role == "candidate":
                history_lines.append(f"Candidate: {content}")
        history_text = "\n".join(history_lines)

        prompt = (
            f"You are NovaAI conducting a PRELIMINARY VOICE SCREENING for the {job_title} role.\n"
            f"Role Context: {skills_str}\n\n"
            f"Conversation Transcript So Far:\n{history_text}\n\n"
            "Screening Purpose: PRELIMINARY assessment — evaluate spoken communication, confidence, "
            "professional tone, and basic role familiarity. Do NOT ask deep technical questions.\n\n"
            "Instructions:\n"
            "1. Based on the candidate's last response, ask ONE concise follow-up question. "
            "Focus on: communication style, professional mindset, teamwork or leadership experience, "
            "or general familiarity with the role area. Keep it conversational and welcoming.\n"
            "2. Keep it natural and under 2 sentences.\n"
            "3. Return ONLY the question text — no preamble, no stage directions, no markdown formatting."
        )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        err = str(e)
        if _is_rate_limit_error(err):
            raise Exception(
                "AI rate limit reached (429). Please wait a moment before continuing the screening."
            )
        if _is_llm_unavailable_error(err):
            raise Exception(
                "AI screening service is temporarily unavailable. Your progress has been saved. Please try again in a moment."
            )
        raise Exception(f"Failed to generate screening question: {err[:300]}")


def generate_screening_assessment(
    job_title: str,
    job_skills: list,
    candidate_name: str,
    candidate_skills: str,
    transcript: list
) -> dict:
    """
    Generate a structured PRELIMINARY assessment JSON from the voice screening transcript.

    This is a PRELIMINARY VOICE SCREENING — NOT a full technical interview.
    It does NOT replicate the AI Interview Assistant.

    The existing assessment fields are returned unchanged:
      overall_score, communication_score, technical_score,
      strengths, areas_for_improvement, recommendation, overall_feedback

    Two NEW fields are MERGED into the same JSON (single LLM call, no extra latency):
      answer_naturalness   — "Natural" | "Possibly Scripted" |
                             "Highly Scripted / Potentially AI-Assisted" | "Unable to Analyze"
      naturalness_feedback — short cautious observation (NOT a guaranteed AI-detection claim)

    Returns a dict. On failure, returns a safe fallback dict (never raises).

    The final Screened / Not Screened decision is derived DETERMINISTICALLY by
    derive_screening_decision() — not by the LLM.
    Threshold: SCREENED = communication_score >= 5.5 AND overall_score >= 5.0

    The naturalness indicator does NOT affect Screened / Not Screened.
    """
    skills_str = ", ".join(
        [s.get("name", "") for s in job_skills if s.get("name")]
    ) if job_skills else "Not specified"

    # Build readable transcript text (candidate turns only for naturalness analysis)
    transcript_lines = []
    candidate_turns_only = []
    for turn in transcript:
        role = turn.get("role", "")
        content = turn.get("content", "")
        if role == "ai":
            transcript_lines.append(f"NovaAI: {content}")
        elif role == "candidate":
            transcript_lines.append(f"Candidate: {content}")
            candidate_turns_only.append(content)
    transcript_text = "\n".join(transcript_lines)

    if not transcript_text.strip():
        return _fallback_assessment("No transcript available — screening may have ended before any responses were recorded.")

    prompt = (
        f"You are NovaAI evaluating a PRELIMINARY VOICE SCREENING session for the {job_title} role.\n"
        f"Candidate: {candidate_name}\n"
        f"Role Context: {skills_str}\n"
        f"Candidate Background: {candidate_skills}\n\n"
        f"Screening Transcript:\n{transcript_text}\n\n"
        "═══════════════════════════════════════════════════════\n"
        "CRITICAL INSTRUCTION — READ CAREFULLY:\n"
        "This is a PRELIMINARY VOICE SCREENING, NOT a full technical interview.\n"
        "You are NOT the AI Interview Assistant. Do NOT evaluate advanced technical knowledge.\n"
        "Do NOT generate a full technical interview assessment.\n"
        "Do NOT penalise candidates for lack of technical depth — this is a communication screen.\n"
        "═══════════════════════════════════════════════════════\n\n"
        "Evaluate the candidate ONLY on these preliminary screening criteria:\n"
        "1. Communication Skills (→ communication_score): Spoken clarity, fluency, articulation, "
        "active listening, and ability to express ideas clearly.\n"
        "2. Confidence & Professionalism: Self-assurance, professional tone, composure, "
        "and presentation quality.\n"
        "3. Leadership & Teamwork Indicators: Observable initiative, collaboration mindset, "
        "or teamwork attitude from spoken responses.\n"
        "4. Basic Domain Familiarity (→ technical_score): General spoken awareness of the role area — "
        "NOT advanced technical knowledge. Score generously if they show basic familiarity.\n"
        "5. Overall Preliminary Suitability (→ overall_score): Is this candidate's communication "
        "and professional presentation sufficient for the next evaluation stage?\n\n"
        "ADDITIONALLY — Answer Naturalness Observation (informational only, not for screening):\n"
        "Analyze whether the candidate's spoken answers APPEAR natural or possibly scripted.\n"
        "Look for signals such as: overly generic answers, excessive buzzwords, template-like phrasing,\n"
        "memorized-sounding responses, lack of personal examples, repetitive/formulaic wording,\n"
        "unusually polished or robotic language, and lack of candidate-specific details.\n"
        "IMPORTANT: This is NOT a guaranteed AI detector. Use cautious observational language only.\n"
        "NEVER claim 'This answer was definitely generated by AI.'\n"
        "Use ONLY one of these labels: \"Natural\", \"Possibly Scripted\", \"Highly Scripted / Potentially AI-Assisted\"\n"
        "If insufficient transcript is available to assess, use \"Unable to Analyze\".\n\n"
        "Provide a structured assessment. Return ONLY valid JSON with exactly this structure:\n"
        "{\n"
        '  "overall_score": <float 0-10>,\n'
        '  "communication_score": <float 0-10>,\n'
        '  "technical_score": <float 0-10>,\n'
        '  "strengths": ["<strength related to communication/confidence/teamwork/professionalism>"],\n'
        '  "areas_for_improvement": ["<area 1 — communication or professional presentation focused>"],\n'
        '  "recommendation": "<Strong Candidate | Consider | Needs Further Evaluation>",\n'
        '  "overall_feedback": "<recruiter-friendly 2-3 sentence summary of spoken communication, '
        'confidence, and preliminary professional suitability — NOT technical skills depth>",\n'
        '  "answer_naturalness": "<Natural | Possibly Scripted | Highly Scripted / Potentially AI-Assisted | Unable to Analyze>",\n'
        '  "naturalness_feedback": "<1-2 sentence cautious observation about response style — do NOT claim AI generation with certainty>"\n'
        "}\n\n"
        "Base all scores strictly on the transcript content. "
        "Do NOT include markdown, code fences, or any text outside the JSON object."
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        raw = response.choices[0].message.content.strip()
        data = json.loads(raw)

        # Validate and sanitise all fields before returning.
        # Existing fields — unchanged.
        # Two new naturalness fields merged in — with safe defaults.
        valid_naturalness_labels = {
            "Natural",
            "Possibly Scripted",
            "Highly Scripted / Potentially AI-Assisted",
            "Unable to Analyze"
        }
        raw_naturalness = str(data.get("answer_naturalness", "Unable to Analyze")).strip()
        if raw_naturalness not in valid_naturalness_labels:
            raw_naturalness = "Unable to Analyze"

        return {
            # ── Existing fields (unchanged) ──────────────────────────────────
            "overall_score": float(data.get("overall_score", 0)),
            "communication_score": float(data.get("communication_score", 0)),
            "technical_score": float(data.get("technical_score", 0)),
            "strengths": list(data.get("strengths", [])),
            "areas_for_improvement": list(data.get("areas_for_improvement", [])),
            "recommendation": str(data.get("recommendation", "Needs Further Evaluation")),
            "overall_feedback": str(data.get("overall_feedback", "Assessment incomplete.")),
            # ── New naturalness fields (informational only) ──────────────────
            "answer_naturalness": raw_naturalness,
            "naturalness_feedback": str(data.get(
                "naturalness_feedback",
                "Insufficient data to assess response naturalness."
            )).strip(),
        }

    except Exception as e:
        err = str(e)
        if _is_rate_limit_error(err):
            return _fallback_assessment(
                "AI rate limit reached (429). The transcript has been saved. "
                "Please try saving the screening again in a moment to generate the assessment."
            )
        if _is_llm_unavailable_error(err):
            return _fallback_assessment(
                "AI screening service is temporarily unavailable. "
                "The transcript has been preserved. Please try again in a moment."
            )
        return _fallback_assessment(
            f"Assessment generation encountered an error. Transcript is preserved. Error: {err[:200]}"
        )


def _fallback_assessment(reason: str) -> dict:
    """Safe fallback returned when AI assessment fails. Never raises.
    Naturalness fields default to Unable to Analyze — never fabricated."""
    return {
        "overall_score": 0.0,
        "communication_score": 0.0,
        "technical_score": 0.0,
        "strengths": [],
        "areas_for_improvement": [],
        "recommendation": "Needs Further Evaluation",
        "overall_feedback": reason,
        "answer_naturalness": "Unable to Analyze",
        "naturalness_feedback": "Assessment could not be completed — naturalness analysis unavailable.",
        "error": True
    }
