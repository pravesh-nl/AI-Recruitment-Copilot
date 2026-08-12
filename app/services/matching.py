import json
import re

from app.services.gemini_skill_service import analyze_all_skills
# ============================================================
# PARSE JSON / LIST DATA
# ============================================================

def parse_data(value):
    """
    Convert JSON/string/list data into a Python list.
    """

    if not value:
        return []

    if isinstance(value, list):
        return value

    try:
        data = json.loads(value)

        if isinstance(data, list):
            return data

        return [data]

    except Exception:
        return [
            item.strip()
            for item in str(value).split(",")
            if item.strip()
        ]


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize_skill(skill):
    """
    Normalize skill names for reliable comparison.
    """

    if not skill:
        return ""

    skill = str(skill).lower().strip()

    skill = re.sub(
        r"[^a-z0-9+#.\- ]",
        "",
        skill
    )

    return skill


# ============================================================
# CANDIDATE SKILLS
# ============================================================

def get_candidate_skills(candidate):

    skills = parse_data(candidate.skills)

    return {
        normalize_skill(skill)
        for skill in skills
        if normalize_skill(skill)
    }
    # ============================================================
# BUILD CANDIDATE EVIDENCE DATA
# ============================================================

def build_candidate_evidence(candidate):

    return {
        "skills": parse_data(candidate.skills),
        "education": parse_data(candidate.education),
        "experience": parse_data(candidate.experience),
        "projects": parse_data(candidate.projects),
        "certifications": parse_data(candidate.certifications)
    }

# ============================================================
# ANALYZE SKILL EVIDENCE
# ============================================================

def analyze_candidate_skill(candidate, skill_name):

    candidate_skills = get_candidate_skills(candidate)

    normalized_skill = normalize_skill(skill_name)

    # --------------------------------------------------------
    # Explicitly listed skill
    # --------------------------------------------------------

    if normalized_skill in candidate_skills:

        return {
            "status": "explicit",
            "confidence": 1.0,
            "evidence": (
                f"{skill_name} is explicitly listed "
                "in the candidate's skills."
            )
        }

    # --------------------------------------------------------
    # Skill not explicitly listed
    # Ask Gemini to look for evidence
    # --------------------------------------------------------

    candidate_data = build_candidate_evidence(candidate)

    analysis = analyze_skill_evidence(
        skill_name,
        candidate_data
    )

    return analysis

# ============================================================
# JOB SKILLS
# ============================================================

def get_job_skills(job):

    skills = parse_data(job.skills)

    result = []

    for skill in skills:

        if isinstance(skill, dict):

            name = skill.get("name", "")
            level = skill.get("level", "Basic")

            result.append({
                "name": normalize_skill(name),
                "level": level
            })

        else:

            result.append({
                "name": normalize_skill(skill),
                "level": "Basic"
            })

    return result


# ============================================================
# EXPERIENCE EXTRACTION
# ============================================================

def extract_experience(candidate):

    if not candidate.experience:
        return 0.0

    experience_list = parse_data(candidate.experience)

    text = " ".join(
        str(item)
        for item in experience_list
    ).lower()

    # Look for explicit experience duration
    patterns = [
        r"(\d+(?:\.\d+)?)\s*\+?\s*years?",
        r"(\d+(?:\.\d+)?)\s*yrs?"
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            return float(match.group(1))

    # Experience exists but exact duration
    # is not explicitly mentioned.
    if experience_list:
        return 1.0

    return 0.0
# ============================================================
# INFER CANDIDATE SKILL LEVEL
# ============================================================


def infer_skill_level(candidate, skill_name):
    """
    Infer candidate skill level using resume evidence.

    Levels:
    Basic        -> limited evidence
    Intermediate -> practical/project/experience evidence
    Advanced     -> strong repeated/professional evidence
    """

    skill_name = normalize_skill(skill_name)

    candidate_skills = get_candidate_skills(candidate)

    if skill_name not in candidate_skills:
        return "Basic"

    # --------------------------------------------------------
    # Gather resume information
    # --------------------------------------------------------

    education = " ".join(
        str(x)
        for x in parse_data(candidate.education)
    ).lower()

    experience = " ".join(
        str(x)
        for x in parse_data(candidate.experience)
    ).lower()

    projects = " ".join(
        str(x)
        for x in parse_data(candidate.projects)
    ).lower()

    certifications = " ".join(
        str(x)
        for x in parse_data(candidate.certifications)
    ).lower()

    # --------------------------------------------------------
    # Evidence score
    # --------------------------------------------------------

    score = 0

    # Explicit skill listing
    if skill_name in candidate_skills:
        score += 1

    # Skill directly mentioned in projects
    if skill_name in projects:
        score += 3

    # Skill directly mentioned in experience
    if skill_name in experience:
        score += 4

    # Skill mentioned in certifications
    if skill_name in certifications:
        score += 2

    # Skill mentioned in education
    if skill_name in education:
        score += 1

    # --------------------------------------------------------
    # Detect years associated with the skill
    # --------------------------------------------------------

    full_text = (
        education
        + " "
        + experience
        + " "
        + projects
        + " "
        + certifications
    )

    skill_year_pattern = (
        rf"{re.escape(skill_name)}"
        r".{0,80}?"
        r"(\d+(?:\.\d+)?)"
        r"\s*\+?\s*years?"
    )

    match = re.search(
        skill_year_pattern,
        full_text
    )

    if match:

        years = float(match.group(1))

        if years >= 3:
            score += 4

        elif years >= 2:
            score += 3

        elif years >= 1:
            score += 2

    # --------------------------------------------------------
    # Infer level
    # --------------------------------------------------------

    if score >= 7:
        return "Advanced"

    elif score >= 4:
        return "Intermediate"

    return "Basic"
# ============================================================
# INFER SKILL LEVEL FROM GEMINI ANALYSIS
# ============================================================

def infer_skill_level_from_analysis(skill_analysis):

    status = skill_analysis.get(
        "status",
        "missing"
    )

    confidence = float(
        skill_analysis.get(
            "confidence",
            0
        )
    )

    evidence = str(
        skill_analysis.get(
            "evidence",
            ""
        )
    ).lower()

    # Missing skill
    if status == "missing":
        return None

    # Strong evidence → Advanced
    strong_keywords = [
        "professional",
        "extensive",
        "multiple projects",
        "multiple years",
        "production",
        "developed",
        "implemented",
        "deployed",
        "worked with"
    ]

    strong_evidence = any(
        keyword in evidence
        for keyword in strong_keywords
    )

    if strong_evidence and confidence >= 0.90:
        return "Advanced"

    # Good practical evidence → Intermediate
    practical_keywords = [
        "project",
        "built",
        "developed",
        "used",
        "implemented",
        "applied",
        "experience"
    ]

    practical_evidence = any(
        keyword in evidence
        for keyword in practical_keywords
    )

    if practical_evidence and confidence >= 0.75:
        return "Intermediate"

    # Explicit listing alone = Basic
    if status == "explicit":
        return "Basic"

    # Inferred with strong confidence
    if status == "inferred" and confidence >= 0.90:
        return "Intermediate"

    return "Basic"
# ============================================================
# CALCULATE SKILL LEVEL SCORE
# ============================================================
# ============================================================
# SKILL LEVEL VALUES
# ============================================================

SKILL_LEVELS = {
    "basic": 1,
    "beginner": 1,
    "intermediate": 2,
    "advanced": 3,
    "expert": 4
}

def calculate_level_score(
    candidate_level,
    required_level
):

    candidate_value = SKILL_LEVELS.get(
        candidate_level.lower(),
        1
    )

    required_value = SKILL_LEVELS.get(
        required_level.lower(),
        1
    )

    if candidate_value >= required_value:
        return 1.0

    return candidate_value / required_value


def calculate_match(candidate, job):

    job_skills = get_job_skills(job)

    matched_skills = []
    missing_skills = []

    total_skill_score = 0

    # --------------------------------------------------------
    # Build candidate evidence
    # --------------------------------------------------------

    candidate_data = {
        "skills": parse_data(candidate.skills),
        "education": parse_data(candidate.education),
        "experience": parse_data(candidate.experience),
        "projects": parse_data(candidate.projects),
        "certifications": parse_data(candidate.certifications)
    }

    # --------------------------------------------------------
    # Get required skill names
    # --------------------------------------------------------

    required_skill_names = [
        skill["name"]
        for skill in job_skills
    ]

    # --------------------------------------------------------
    # Analyze ALL skills in ONE Gemini request
    # --------------------------------------------------------

    try:
        all_skill_analysis = analyze_all_skills(
            required_skill_names,
            candidate_data
        )
    except Exception as e:
        print(
            f"[WARNING] Gemini skill analysis unavailable: {e}"
        )

        all_skill_analysis = []

        # Fallback to local skill detection
        for skill_name in required_skill_names:

            normalized = normalize_skill(skill_name)

            if normalized in candidate_skills:
                all_skill_analysis.append({
                    "skill": skill_name,
                    "status": "explicit",
                    "confidence": 1.0,
                    "evidence": (
                        f"{skill_name} is explicitly listed "
                        "in the candidate's skills."
                    )
                })
            else:
                all_skill_analysis.append({
                    "skill": skill_name,
                    "status": "missing",
                    "confidence": 0.0,
                    "evidence": (
                        f"{skill_name} was not found in "
                        "the candidate's explicitly listed skills."
                    )
                })
        # ========================================================
    # FALLBACK IF GEMINI IS UNAVAILABLE
    # ========================================================

    if not all_skill_analysis:

        all_skill_analysis = []

        for skill in required_skill_names:

            if skill in candidate_skills:

                all_skill_analysis.append({
                    "skill": skill,
                    "status": "explicit",
                    "confidence": 1.0,
                    "evidence": (
                        f"{skill} is explicitly listed "
                        "in the candidate's skills."
                    )
                })

            else:

                all_skill_analysis.append({
                    "skill": skill,
                    "status": "missing",
                    "confidence": 0.0,
                    "evidence": (
                        "No explicit skill match found."
                    )
                })

    # --------------------------------------------------------
    # Create lookup map
    # --------------------------------------------------------

    skill_analysis_map = {
        normalize_skill(item["skill"]): item
        for item in all_skill_analysis
    }

    # --------------------------------------------------------
    # Match each required skill
    # --------------------------------------------------------

    for required_skill in job_skills:

        skill_name = required_skill["name"]
        required_level = required_skill["level"]

        skill_analysis = skill_analysis_map.get(
            normalize_skill(skill_name),
            {
                "skill": skill_name,
                "status": "missing",
                "confidence": 0,
                "evidence": "No analysis available."
            }
        )

        status = skill_analysis.get(
            "status",
            "missing"
        )

        confidence = float(
            skill_analysis.get(
                "confidence",
                0
            )
        )

        evidence = skill_analysis.get(
            "evidence",
            ""
        )

        # ----------------------------------------------------
        # Missing skill
        # ----------------------------------------------------

        if status == "missing":

            missing_skills.append({

                "name": skill_name,

                "required_level":
                    required_level,

                "candidate_level":
                    None,

                "evidence":
                    evidence,

                "confidence":
                    confidence,

                "status":
                    "missing"
            })

            continue

        # ----------------------------------------------------
        # Determine candidate skill level
        # ----------------------------------------------------

        candidate_level = infer_skill_level_from_analysis(
            skill_analysis
        )

        if not candidate_level:
            candidate_level = "Basic"

        # ----------------------------------------------------
        # Calculate level score
        # ----------------------------------------------------

        level_score = calculate_level_score(
            candidate_level,
            required_level
        )

        # ----------------------------------------------------
        # Confidence adjustment for inferred skills
        # ----------------------------------------------------

        if status == "inferred":

            level_score *= confidence

        total_skill_score += level_score

        # ----------------------------------------------------
        # Store matched skill
        # ----------------------------------------------------

        matched_skills.append({

            "name":
                skill_name,

            "required_level":
                required_level,

            "candidate_level":
                candidate_level,

            "level_match":
                candidate_level.lower()
                in [
                    required_level.lower(),
                    "advanced",
                    "expert"
                ],

            "status":
                status,

            "confidence":
                confidence,

            "evidence":
                evidence
        })

    # --------------------------------------------------------
    # Skill Score = 80%
    # --------------------------------------------------------

    if job_skills:

        skill_score = (
            total_skill_score
            / len(job_skills)
        ) * 80

    else:

        skill_score = 80

    # --------------------------------------------------------
    # Experience Score = 20%
    # --------------------------------------------------------

    candidate_experience = extract_experience(
        candidate
    )

    required_experience = (
        job.min_experience or 0
    )

    if required_experience <= 0:

        experience_score = 20

    elif candidate_experience >= required_experience:

        experience_score = 20

    else:

        experience_score = (
            candidate_experience
            / required_experience
        ) * 20

    # --------------------------------------------------------
    # Final Score
    # --------------------------------------------------------

    final_score = round(
        skill_score + experience_score
    )

    final_score = max(
        0,
        min(final_score, 100)
    )

    # --------------------------------------------------------
    # Match Level
    # --------------------------------------------------------

    if final_score >= 85:

        match_level = "Excellent Match"

    elif final_score >= 70:

        match_level = "Strong Match"

    elif final_score >= 50:

        match_level = "Moderate Match"

    else:

        match_level = "Low Match"

    # --------------------------------------------------------
    # Result
    # --------------------------------------------------------

    return {

        "candidate_id":
            candidate.id,

        "candidate_name":
            candidate.name,

        "email":
            candidate.email,

        "match_score":
            final_score,

        "match_level":
            match_level,

        "matched_skills":
            matched_skills,

        "missing_skills":
            missing_skills,

        "candidate_experience":
            candidate_experience,

        "required_experience":
            required_experience,

        "skill_gap":
            missing_skills
    }


# ============================================================
# SKILL GAP ANALYSIS
# ============================================================

def generate_skill_gap(result):

    missing_skills = result.get(
        "missing_skills",
        []
    )

    if not missing_skills:

        return {

            "has_skill_gap":
                False,

            "message":
                "Candidate has all required skills.",

            "missing_skills":
                [],

            "recommendations":
                []
        }

    recommendations = []

    for skill in missing_skills:

        if isinstance(skill, dict):

            skill_name = skill.get(
                "name",
                ""
            )

            required_level = skill.get(
                "required_level",
                "Basic"
            )

            recommendations.append(
                f"Candidate should improve "
                f"{skill_name} to {required_level} level."
            )

        else:

            recommendations.append(
                f"Candidate should improve "
                f"{skill}."
            )

    return {

        "has_skill_gap":
            True,

        "message":
            "Candidate is missing some required skills.",

        "missing_skills":
            missing_skills,

        "recommendations":
            recommendations
    }