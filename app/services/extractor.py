import re

import spacy

from spacy.matcher import PhraseMatcher



nlp = spacy.load("en_core_web_lg")



SKILLS = [
    # Programming
    "Python","Java","C","C++","C#","JavaScript","TypeScript","PHP","Go","Rust",

    # Web
    "HTML","CSS","React","Angular","Vue","Next.js","Node.js","Express","Bootstrap",

    # Backend
    "FastAPI","Flask","Django","Spring Boot",".NET","REST API","GraphQL",

    # Database
    "SQL","MySQL","PostgreSQL","SQLite","MongoDB","Redis","Oracle",

    # Cloud
    "AWS","Azure","GCP","Docker","Kubernetes","Linux","Git","GitHub","CI/CD",

    # AI/ML
    "Machine Learning","Deep Learning","NLP","Computer Vision",
    "TensorFlow","PyTorch","Scikit-learn","OpenCV","Pandas","NumPy",

    # Security
    "Cybersecurity","Network Security","Penetration Testing",
    "Risk Assessment","Incident Response",

    # Business
    "Project Management","Leadership","Communication",
    "Teamwork","Problem Solving","Time Management",

    # Finance
    "Accounting","Bookkeeping","Financial Analysis",

    # Marketing
    "SEO","SEM","Digital Marketing","Content Writing",

    # HR
    "Recruitment","Talent Acquisition","Payroll",

    # Healthcare
    "Patient Care","Medical Coding","EMR",

    # Security Guard
    "Safety Compliance",
    "Investigation",
    "Criminal Justice",
    "Surveillance",
    "CCTV",
    "Physical Security",
    "Access Control",
    "Security Patrol",
    "Incident Reporting",
    "Martial Arts",
    "Combat Training",
    "Fire Safety",
    "Emergency Response"
]



matcher = PhraseMatcher(nlp.vocab, attr="LOWER")

patterns = [nlp.make_doc(skill) for skill in SKILLS]

matcher.add("SKILLS", patterns)


# ---------------------------------------------------------------------------
# KNOWN LOCATIONS — used for multi-layer name validation.
# A word matching this set will NEVER be accepted as (part of) a candidate name.
# This list covers Indian cities/districts/states and common international cities
# that commonly appear near the top of resumes.
# ---------------------------------------------------------------------------
KNOWN_LOCATIONS = {
    # Rajasthan cities / districts
    "jhunjhunu", "jhunjhun", "sikar", "churu", "jaipur", "jodhpur", "udaipur",
    "kota", "ajmer", "bikaner", "alwar", "bharatpur", "bhilwara", "pali",
    "nagaur", "dungarpur", "barmer", "jaisalmer", "sirohi", "tonk", "bundi",
    "rajsamand", "banswara", "dholpur", "karauli", "dausa", "ganganagar",
    "hanumangarh", "pratapgarh", "sawai", "madhopur", "chittorgarh",
    "rajasthan",

    # Major Indian cities / states
    "delhi", "mumbai", "bangalore", "bengaluru", "hyderabad", "chennai",
    "kolkata", "pune", "ahmedabad", "surat", "lucknow", "kanpur", "nagpur",
    "indore", "thane", "bhopal", "visakhapatnam", "pimpri", "chinchwad",
    "patna", "vadodara", "ghaziabad", "ludhiana", "agra", "nashik",
    "faridabad", "meerut", "rajkot", "varanasi", "srinagar", "aurangabad",
    "dhanbad", "amritsar", "allahabad", "prayagraj", "ranchi", "haora",
    "coimbatore", "jabalpur", "gwalior", "vijayawada", "madurai", "raipur",
    "kochi", "chandigarh", "guwahati", "solapur", "hubli", "mysuru",
    "tiruchirappalli", "bareilly", "aligarh", "moradabad", "noida", "gurugram",
    "gurgaon", "navi", "navi mumbai", "thane", "jamshedpur", "bhilai",
    "cuttack", "firozabad", "kota", "rohtak", "bikaner", "jalandhar",
    "saharanpur", "gorakhpur", "guntur", "warangul", "raurkela",
    "kashmir", "jammu", "shimla", "dehradun", "nainital", "mussoorie",
    "kerala", "goa", "assam", "bihar", "odisha", "orissa", "punjab",
    "haryana", "gujarat", "maharashtra", "uttarakhand", "himachal",
    "chhattisgarh", "jharkhand", "telangana", "karnataka", "tamilnadu",
    "tamil", "andhra", "pradesh", "west", "uttar", "madhya", "arunachal",
    "meghalaya", "manipur", "nagaland", "tripura", "mizoram", "sikkim",

    # International cities
    "london", "new york", "new", "york", "paris", "berlin", "tokyo",
    "singapore", "dubai", "toronto", "sydney", "melbourne", "chicago",
    "houston", "boston", "seattle", "san", "francisco", "angeles", "los",
    "washington", "dubai", "abu", "dhabi", "riyadh", "bahrain", "qatar",

    # Generic location words
    "india", "usa", "uk", "uae", "canada", "australia", "germany",
    "street", "road", "nagar", "colony", "sector", "block", "ward",
    "district", "city", "state", "country", "pin", "zip", "pincode",
    "area", "village", "town", "tehsil", "taluk",
}

# Words that are never part of a human name (technical, job-title, project noise)
NAME_POISON_WORDS = {
    # Technical / AI / ML
    "ai", "ml", "machine", "learning", "deep", "predictive",
    "neural", "nlp", "computer", "vision", "analytics", "analysis",
    "algorithm", "model", "data", "science", "scientist",
    # Project / product words
    "black", "box", "system", "project", "platform", "framework",
    "application", "app", "dashboard", "tool", "engine", "pipeline",
    "powered", "failure", "maintenance", "detection", "prediction",
    "building", "using",
    # Programming languages / tech
    "python", "java", "javascript", "typescript", "react", "angular",
    "node", "flask", "django", "fastapi", "sql", "mysql",
    "mongodb", "aws", "azure", "gcp", "docker", "kubernetes",
    "github", "git", "linux", "html", "css", "api",
    # Job titles / professional headlines
    "developer", "engineer", "analyst", "manager", "consultant",
    "architect", "designer", "specialist", "lead", "senior",
    "junior", "intern", "researcher",
    # Generic resume noise
    "enthusiast", "professional", "experienced", "certified",
}

# Common resume section headings and non-name lines
NAME_BLACKLIST = {
    "resume", "curriculum vitae", "cv", "contact",
    "contact information", "objective", "profile", "summary",
    "education", "experience", "work experience", "projects",
    "certifications", "skills", "technical skills", "languages",
    "interests", "hobbies", "references", "email", "phone",
    "mobile", "details", "links", "name", "full name",
    "address", "location", "linkedin", "github", "first name", "last name",
}

# Section headings that mark where the header block ends.
SECTION_MARKERS = {
    "summary", "professional summary", "objective", "profile",
    "education", "experience", "work experience", "skills",
    "technical skills", "projects", "certifications",
    "employment history", "internship", "internships",
}

# Explicit name field labels — Strategy 0 looks for these patterns.
# e.g. "Name: Rahul Sharma" or "Full Name: Rahul Sharma"
EXPLICIT_NAME_LABELS = [
    r"full\s+name",
    r"candidate\s+name",
    r"applicant\s+name",
    r"name",
]
# Pre-compiled pattern: "Label : Value" at the start of a line (case-insensitive)
_EXPLICIT_NAME_RE = re.compile(
    r"^\s*(?:" + "|".join(EXPLICIT_NAME_LABELS) + r")\s*[:\-]\s*(.+)$",
    re.IGNORECASE
)


def extract_section(text, section_names):
    """
    Returns the content under a heading until the next heading.
    """

    lines = text.splitlines()

    start = None

    for i, line in enumerate(lines):

        clean = line.strip().lower()

        if any(name in clean for name in section_names):
            start = i + 1
            break

    if start is None:
        return ""

    collected = []

    for line in lines[start:]:

        clean = line.strip()

        if (
            clean.isupper()
            and len(clean.split()) <= 5
        ):
            break

        if clean.lower() in [
            "education",
            "experience",
            "work experience",
            "employment history",
            "professional experience",
            "projects",
            "certifications",
            "skills",
            "technical skills",
            "profile",
            "summary",
            "details",
            "links",
            "languages",
            "interests",
            "hobbies",
            "references"
            ]:
            break
        # Skip decorative separator lines
        if re.fullmatch(r"[=─═\-_*•\s]{5,}", clean):
            continue

        collected.append(clean)

    return "\n".join(collected)


def _is_name_line(line: str) -> bool:
    """
    Returns True if `line` looks like a standalone human name.

    Multi-layer validation:
      Layer 1 — Exact blacklist match (section headings, reserved words)
      Layer 2 — Contact/URL signal rejection
      Layer 3 — Digit rejection
      Layer 4 — Special character / separator rejection
      Layer 5 — Known location word rejection  ← new, addresses the Jhunjhunu problem
      Layer 6 — Technical / job-title poison word rejection
      Layer 7 — Length and alpha-only structure check
      Layer 8 — spaCy PERSON entity cross-check (optional, used in Strategy 1 only)

    A location is NEVER accepted based on position alone.
    """
    clean = line.strip()
    lower = clean.lower()

    # Layer 1: Exact section heading / blacklisted phrase
    if lower in NAME_BLACKLIST:
        return False

    # Layer 2: Contact / URL signals
    if any(kw in lower for kw in [
        "cgpa", "gpa", "@", "email", "phone", "mobile",
        "linkedin", "github", "http", "www.", "|", "/",
    ]):
        return False

    # Layer 3: Lines with digits (phone numbers, years, roll numbers, etc.)
    if any(ch.isdigit() for ch in clean):
        return False

    # Layer 4: Special character / separator signals
    if any(ch in clean for ch in ["|", "/", ",", "(", ")"]):
        return False

    # Layer 5: Known location word rejection.
    # ANY word in the line that is a known location → reject the whole line.
    words_lower = lower.split()
    if any(w in KNOWN_LOCATIONS for w in words_lower):
        return False

    # Layer 6: Technical / job-title poison words
    if any(w in NAME_POISON_WORDS for w in words_lower):
        return False

    # Layer 7: Structure — a human name is 2–4 words, all alphabetic (hyphens/apostrophes allowed)
    words = clean.split()
    if not (2 <= len(words) <= 4):
        return False

    if not all(w.replace("-", "").replace("'", "").isalpha() for w in words):
        return False

    return True


def _find_header_boundary(lines) -> int:
    """
    Returns the index of the first line that looks like a section heading.
    The name must appear before this boundary.
    """
    for i, line in enumerate(lines):
        if line.strip().lower() in SECTION_MARKERS:
            return i
    # If no section found within first 30 lines, use 30 as soft limit
    return min(30, len(lines))


def extract_candidate_details(text):

    data = {
        "name": "",
        "name_source": "Not Available",
        "email": "",
        "phone": "",
        "skills": [],
        "education": [],
        "projects": [],
        "certifications": [],
        "experience": []
    }

    doc = nlp(text)

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    # ================================================================
    # NAME EXTRACTION — four strategies in priority order.
    # A location is NEVER accepted based on position alone.
    # Multi-layer _is_name_line() validation is applied to every
    # candidate string regardless of how it was found.
    # ================================================================

    # ----------------------------------------------------------------
    # STRATEGY 0 (HIGHEST PRIORITY): Explicit name field label.
    # Looks for patterns like "Name: Rahul Sharma", "Full Name: ...",
    # "Candidate Name: ...", "Applicant Name: ..." in the first 20 lines.
    # ----------------------------------------------------------------
    header_boundary = _find_header_boundary(lines)
    search_limit = min(header_boundary, 20)

    for line in lines[:search_limit]:
        m = _EXPLICIT_NAME_RE.match(line)
        if m:
            value = m.group(1).strip()
            # Still validate — the value after the label must pass all guards
            if _is_name_line(value):
                data["name"] = value.title()
                data["name_source"] = "Explicit Name Field"
                break
            # If it fails validation, do not use it; try next strategy

    # ----------------------------------------------------------------
    # STRATEGY 1 (FALLBACK): Scan the top of the resume.
    # The candidate name is often the first meaningful non-contact,
    # non-heading line before any section marker.
    # Every candidate line is validated with _is_name_line().
    # ----------------------------------------------------------------
    if not data["name"]:
        for line in lines[:search_limit]:
            if _is_name_line(line):
                data["name"] = line.strip().title()
                data["name_source"] = "Resume Header"
                break

    # ----------------------------------------------------------------
    # STRATEGY 2 (FALLBACK): spaCy PERSON NER.
    # Guards:
    #   a) Entity text must pass _is_name_line() (includes location check)
    #   b) Entity must appear in top 25% or first 300 chars of document
    #   c) Prefer the earliest PERSON entity in that window
    # ----------------------------------------------------------------
    if not data["name"]:
        doc_len = len(text)
        top_cutoff = max(300, int(doc_len * 0.25))  # first 25% or 300 chars

        best_name = ""
        best_start = doc_len  # lower (earlier) is better

        for ent in doc.ents:
            if ent.label_ != "PERSON":
                continue

            candidate_text = ent.text.strip()

            # Must pass the full multi-layer name validation (including location guard)
            if not _is_name_line(candidate_text):
                continue

            # Must appear in the top portion of the document
            if ent.start_char > top_cutoff:
                continue

            # Prefer the earliest PERSON entity
            if ent.start_char < best_start:
                best_start = ent.start_char
                best_name = candidate_text

        if best_name:
            data["name"] = best_name.title()
            data["name_source"] = "NER / Name Extraction"

    # ----------------------------------------------------------------
    # Final guard: if all strategies failed to find a valid name,
    # return a clean "Name not provided" rather than an empty string.
    # NEVER invent or guess a name.
    # ----------------------------------------------------------------
    if not data["name"]:
        data["name"] = "Name not provided"
        data["name_source"] = "Not Available"

    # -----------------------------
    # EMAIL
    # -----------------------------
    email = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)

    if email:
        data["email"] = email.group()

    # -----------------------------
    # PHONE
    # -----------------------------
    phone = re.search(r'(\+?\d[\d\s-]{8,15}\d)', text)

    if phone:
        data["phone"] = phone.group()

    # -----------------------------
    # SKILLS
    # -----------------------------
    skills_text = extract_section(
        text,
        [
            "skills",
            "technical skills",
            "core competencies",
            "competencies",
            "expertise",
            "technical expertise"
        ]
    )

    skills = set()

    # Extract predefined skills using spaCy matcher
    skill_doc = nlp(skills_text)
    matches = matcher(skill_doc)

    for _, start, end in matches:
        skills.add(skill_doc[start:end].text)

    # Extract bullet points / comma-separated skills
    for line in skills_text.splitlines():

        line = (
            line.replace("•", "")
                .replace("▪", "")
                .replace("-", "")
                .replace("|", ",")
        )

        for part in line.split(","):

            part = part.strip()

            if 2 <= len(part) <= 50:
                skills.add(part)

    data["skills"] = sorted(skills)


    # -----------------------------
    # EDUCATION
    # -----------------------------

    education_text = extract_section(
        text,
        [
            "education",
            "academic qualifications",
            "qualification",
            "academics",
            "education details"
        ]
    )

    education_lines = [
        line.strip()
        for line in education_text.splitlines()
        if line.strip()
    ]

    degrees = [

        "Bachelor",
        "Bachelor of Technology",
        "Bachelor of Engineering",
        "Bachelor of Science",
        "Bachelor of Computer Applications",

        "Master",
        "Master of Technology",
        "Master of Engineering",
        "Master of Science",
        "Master of Computer Applications",
        "Master of Business Administration",

        "B.Tech",
        "B.E",
        "BCA",
        "MCA",
        "M.Tech",
        "M.E",
        "MBA",
        "B.Sc",
        "M.Sc",

        "Diploma",

        "Higher Secondary",
        "Senior Secondary",

        "12th",
        "10th",

        "PhD",
        "Doctorate"
    ]

    for line in education_lines:

        if any(degree.lower() in line.lower() for degree in degrees):

            if line not in data["education"]:

                data["education"].append(line)
    universities = [
        "University",
        "College",
        "Institute",
        "School",
        "Academy"
    ]

    for line in education_lines:

        if any(word.lower() in line.lower() for word in universities):

            if line not in data["education"]:

                data["education"].append(line)
    for line in education_lines:

        if (
            "cgpa" in line.lower()
            or "%"
            in line
            or "percentage"
            in line.lower()
        ):

            if line not in data["education"]:

                data["education"].append(line)    

    # -----------------------------
    # PROJECTS
    # -----------------------------

    project_text = extract_section(
        text,
        [
            "projects",
            "academic projects",
            "personal projects",
            "major projects",
            "key projects",
            "project"
        ]
    )

    if project_text:

        current_project = ""

        for line in project_text.splitlines():

            line = line.strip()

            if not line:
                continue

            # Skip description bullets
            if line.startswith(("•", "-", "*")):
                continue

            # Short lines are usually project titles
            if len(line.split()) <= 10:

                if current_project:
                    data["projects"].append(current_project)

                current_project = line

        if current_project:
            data["projects"].append(current_project)

    else:

        project_keywords = [
            "developed",
            "designed",
            "implemented",
            "created",
            "built",
            "project",
            "system",
            "application",
            "dashboard",
            "website",
            "chatbot",
            "tracker"
        ]

        for line in lines:

            lower = line.lower()

            if any(word in lower for word in project_keywords):

                if line not in data["projects"]:

                    data["projects"].append(line)


    # -----------------------------
    # CERTIFICATIONS
    # -----------------------------

    certification_text = extract_section(
        text,
        [
            "certifications",
            "certification",
            "licenses",
            "licenses & certifications",
            "courses",
            "online courses",
            "professional certifications",
            "training"
        ]
    )

    if certification_text:

        for line in certification_text.splitlines():

            line = line.strip()

            if not line:
                continue

            if line.startswith(("•", "-", "*")):
                line = line[1:].strip()

            if line not in data["certifications"]:
                data["certifications"].append(line)

    else:

        certification_keywords = [
            "certified",
            "certificate",
            "certification",
            "course",
            "coursera",
            "udemy",
            "edx",
            "nptel",
            "infosys",
            "oracle",
            "ibm",
            "google",
            "microsoft",
            "aws",
            "azure",
            "cisco",
            "linkedin learning",
            "simplilearn",
            "great learning"
        ]

        for line in lines:

            lower = line.lower()

            if any(keyword in lower for keyword in certification_keywords):

                if line not in data["certifications"]:
                    data["certifications"].append(line)

    # -----------------------------
    # EXPERIENCE / INTERNSHIPS
    # -----------------------------

    experience_text = extract_section(
        text,
        [
            "experience",
            "work experience",
            "professional experience",
            "employment history",
            "internship",
            "internships",
            "industrial training"
        ]
    )
    for line in experience_text.splitlines():

        line = line.strip()

        if not line:
            continue

        # Ignore separators
        if re.fullmatch(r"[=─═\-_*•\s]{5,}", line):
            continue

        # Ignore very short fragments
        if len(line.split()) < 2:
            continue

        data["experience"].append(line)

    else:

        experience_keywords = [
            "intern",
            "internship",
            "software engineer",
            "developer",
            "engineer",
            "analyst",
            "assistant",
            "executive",
            "consultant",
            "manager",
            "worked",
            "experience"
        ]

        for line in lines:

            lower = line.lower()

            if any(word in lower for word in experience_keywords):

                if line not in data["experience"]:

                    data["experience"].append(line)

    return data