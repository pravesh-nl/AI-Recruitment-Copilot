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

def extract_candidate_details(text):



    data = {

        "name": "",

        "email": "",

        "phone": "",

        "skills": [],

        "education": [],

        "projects": [],

        "certifications": [],

        "experience": []

    }



    doc = nlp(text)



    # -----------------------------

    # NAME

    # -----------------------------


    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    # ----------------------------------------------------------------
    # Words that strongly suggest a line is NOT a candidate name.
    # These include technical terms, project-related words, job titles,
    # and other resume section noise.
    # ----------------------------------------------------------------
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
        # Locations / contact
        "india", "usa", "uk", "street", "city", "state", "country",
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
    # A name must appear BEFORE any of these.
    SECTION_MARKERS = {
        "summary", "professional summary", "objective", "profile",
        "education", "experience", "work experience", "skills",
        "technical skills", "projects", "certifications",
        "employment history", "internship", "internships",
    }

    def _is_name_line(line: str) -> bool:
        """
        Returns True if `line` looks like a standalone human name.
        Applies every rejection heuristic defined above.
        """
        clean = line.strip()
        lower = clean.lower()

        # Reject exact section headings / blacklisted phrases
        if lower in NAME_BLACKLIST:
            return False

        # Reject lines with contact / URL signals
        if any(kw in lower for kw in [
            "cgpa", "gpa", "@", "email", "phone", "mobile",
            "linkedin", "github", "http", "www.", "|", "/",
        ]):
            return False

        # Reject lines that contain digits
        if any(ch.isdigit() for ch in clean):
            return False

        # Reject lines that look like job-title headlines
        # (contain pipe separators, slashes, commas, or parentheses)
        if any(ch in clean for ch in ["|", "/", ",", "(", ")"]):
            return False

        # Reject lines with poisoned technical / project words
        words_lower = lower.split()
        if any(w in NAME_POISON_WORDS for w in words_lower):
            return False

        # A human name is normally 2–4 words, all alphabetic
        words = clean.split()
        if not (2 <= len(words) <= 4):
            return False

        if not all(w.replace("-", "").replace("'", "").isalpha() for w in words):
            return False

        return True

    def _find_header_boundary(lines) -> int:
        """
        Returns the index of the first line that looks like a section
        heading.  The name must appear before this boundary.
        """
        for i, line in enumerate(lines):
            if line.strip().lower() in SECTION_MARKERS:
                return i
        # If no section found within first 30 lines, use 30 as soft limit
        return min(30, len(lines))

    # ----------------------------------------------------------------
    # STRATEGY 1 (PRIMARY): Scan the very top of the resume.
    # The candidate name is almost always the first meaningful line
    # before any contact info / section heading.
    # ----------------------------------------------------------------
    header_boundary = _find_header_boundary(lines)
    # Search within header block (capped at 20 lines for safety)
    search_limit = min(header_boundary, 20)

    for line in lines[:search_limit]:
        if _is_name_line(line):
            data["name"] = line.strip().title()
            break

    # ----------------------------------------------------------------
    # STRATEGY 2 (FALLBACK): Use spaCy PERSON NER — but only if the
    # top-line scan found nothing AND the entity passes all guards.
    #
    # Key guards:
    #  a) The entity text must pass the same _is_name_line() filter.
    #  b) The entity must appear in the TOP PORTION of the full text
    #     (character offset within first 25 % of document).
    #  c) The entity must NOT appear after a section heading marker.
    # ----------------------------------------------------------------
    if not data["name"]:
        doc_len = len(text)
        top_cutoff = max(300, int(doc_len * 0.25))  # first 25 % or 300 chars

        best_name = ""
        best_start = doc_len  # lower (earlier) is better

        for ent in doc.ents:
            if ent.label_ != "PERSON":
                continue

            candidate_name = ent.text.strip()

            # Must pass the same name-line filter
            if not _is_name_line(candidate_name):
                continue

            # Must appear in the top portion of the document
            if ent.start_char > top_cutoff:
                continue

            # Prefer the earliest PERSON entity
            if ent.start_char < best_start:
                best_start = ent.start_char
                best_name = candidate_name

        if best_name:
            data["name"] = best_name.title()

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