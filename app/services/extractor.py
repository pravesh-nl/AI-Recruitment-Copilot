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

    # Common resume headings / unwanted text
    name_blacklist = {
        "resume",
        "curriculum vitae",
        "cv",
        "contact",
        "contact information",
        "objective",
        "profile",
        "summary",
        "education",
        "experience",
        "work experience",
        "projects",
        "certifications",
        "skills",
        "technical skills",
        "languages",
        "interests",
        "hobbies",
        "references",
        "email",
        "phone",
        "mobile",
        "Email"
    }

    # First try spaCy PERSON entities
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            candidate_name = ent.text.strip()
            words = candidate_name.split()

            if (
                2 <= len(words) <= 4
                and all(word.replace("-", "").replace("'", "").isalpha()
                        for word in words)
            ):
                data["name"] = candidate_name
                break

    # Fallback: inspect first few resume lines
    if not data["name"]:

        for line in lines[:15]:

            clean = line.strip()
            lower = clean.lower()

            # Reject obvious non-name lines
            if lower in name_blacklist:
                continue

            if any(
                keyword in lower
                for keyword in [
                    "cgpa",
                    "gpa",
                    "email",
                    "phone",
                    "mobile",
                    "linkedin",
                    "github",
                    "http",
                    "www."
                ]
            ):
                continue

            # Reject lines containing numbers
            if any(char.isdigit() for char in clean):
                continue

            # A normal name should contain 2–4 words
            words = clean.split()

            if not (2 <= len(words) <= 4):
                continue

            # Only alphabetic name-like words
            if all(
                word.replace("-", "").replace("'", "").isalpha()
                for word in words
            ):
                data["name"] = clean.title()
                data["name"] = (
                data["name"]
                .replace("Email", "")
                .replace("EMAIL", "")
                .strip()
            )
                break

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