# AI-Driven Smart Hiring Platform with Candidate Matching Copilot

An AI-powered recruitment platform that automates **resume parsing, candidate profiling, job-based candidate matching, skill analysis, candidate ranking, and skill-gap identification**.

The platform is designed to reduce manual resume screening and provide recruiters with a more consistent and explainable candidate evaluation workflow.

---

## 1. Project Overview

Traditional recruitment requires recruiters to manually read resumes, extract candidate information, compare skills with job requirements, evaluate experience, and identify missing skills.

This project automates these activities by:

* Processing resumes automatically
* Creating structured candidate profiles
* Managing job requirements
* Comparing candidates with selected jobs
* Using an LLM for skill and proficiency analysis
* Calculating candidate hiring scores
* Ranking candidates
* Identifying skill gaps

The project currently covers two completed milestones:

* **Milestone 1:** Resume Parsing & Candidate Profiling
* **Milestone 2:** Candidate Matching & Skill-Gap Analysis

---

# 2. Problem Statement

Recruiters often receive a large number of resumes with different formats and layouts. Manually screening these resumes is time-consuming and can lead to inconsistent evaluation.

The platform addresses this problem by converting unstructured resumes into structured candidate profiles and then comparing those profiles against specific job requirements.

---

# 3. Solution Workflow

```text
             RESUME
                │
                ▼
         Resume Upload
                │
                ▼
       PDF / DOCX Parsing
                │
                ▼
     Candidate Information
          Extraction
                │
                ▼
      Structured Candidate
            Profile
                │
                ▼
           Database
                │
                ▼
       Job Creation/Selection
                │
                ▼
      Job Requirements
      + Required Skills
      + Skill Levels
      + Experience
                │
                ▼
       Candidate Matching
                │
                ▼
       AI Skill Analysis
                │
                ▼
       Skill Gap Analysis
                │
                ▼
        Hiring Score
       80% Skills
       20% Experience
                │
                ▼
       Ranked Candidates
```

---

# 4. Milestone 1 — Resume Parsing & Candidate Profiling

## Objective

Milestone 1 establishes the candidate-data foundation of the platform.

It converts unstructured PDF/DOCX resumes into structured candidate profiles that can be stored in the database and reused by the matching system.

### Main Features

* Resume upload and processing
* PDF/DOCX text extraction
* Candidate name extraction
* Email and phone extraction
* Skill extraction
* Education extraction
* Location extraction
* Experience extraction
* Candidate profile creation
* Database storage
* Candidate retrieval APIs
* Frontend candidate display

---

## Milestone 1 Workflow

1. Recruiter uploads a resume.
2. FastAPI receives the uploaded file.
3. Resume text is extracted.
4. Candidate information is identified.
5. Extracted information is normalized and validated.
6. Candidate profile is stored in the database.
7. Backend APIs provide the processed candidate information.
8. Frontend displays the candidate profile.

---

# 5. Milestone 1 — Backend Architecture

The backend follows a modular structure where API routes, business logic, database models, and schemas are separated.

This makes the system easier to maintain and allows the parsing system to be reused by later modules.

| Component                      | Purpose                                                |
| ------------------------------ | ------------------------------------------------------ |
| `app/main.py`                  | FastAPI application entry point and route registration |
| `app/database.py`              | Database connection and session management             |
| `app/routes/upload.py`         | Receives resume uploads and starts processing          |
| `app/routes/candidate.py`      | Provides candidate retrieval APIs                      |
| `app/services/parser.py`       | Handles resume/document parsing                        |
| `app/services/extractor.py`    | Extracts candidate fields from parsed content          |
| `app/models/candidate.py`      | Defines the candidate database model                   |
| `app/models/upload_history.py` | Tracks upload/processing information                   |
| `app/schemas/`                 | Defines structured API request/response data           |

---

# 6. Resume Parsing & Extraction

The resume processing pipeline converts an unstructured resume into structured candidate information.

The system separates:

### Parser

`parser.py`

Responsible for processing the uploaded document and extracting usable text/content from supported resume formats.

### Extractor

`extractor.py`

Responsible for identifying meaningful candidate fields from the parsed content.

These can include:

* Name
* Email
* Phone
* Skills
* Education
* Location
* Experience

This separation makes it easier to improve extraction logic without changing the upload/API layer.

### Important Consideration

Different resumes use different layouts. Therefore, extraction cannot depend only on fixed positions.

Name extraction also requires validation because headings such as:

```text
Full Name
Candidate Profile
Black Box
Experience
```

or other prominent text can sometimes be incorrectly interpreted as a person's name.

The system should only store information supported by the resume rather than inventing missing information.

---

# 7. Database

The database provides persistent storage for processed candidate profiles.

The project uses:

* **SQLite** as the database
* **SQLAlchemy** for database interaction

Candidate information is stored so that the matching engine can later reuse the extracted profile without parsing the original resume again.

The database contains information related to candidates and upload/processing history.

---

# 8. Milestone 2 — Candidate Matching & Skill-Gap Analysis

## Objective

Milestone 2 uses the structured candidate profiles created in Milestone 1 and compares them against job requirements.

The system evaluates:

* Required skills
* Candidate skills
* Required skill level
* Candidate proficiency level
* Candidate experience
* Missing skills
* Skill-level gaps
* Overall candidate suitability

### Main Features

* Job creation
* Job requirement management
* Required experience
* Required skills
* Basic/Intermediate/Expert skill levels
* Candidate-job matching
* Candidate ranking
* AI skill analysis
* Hiring score calculation
* Skill-gap analysis

---

# 9. Groq + LLM Skill Analysis

The platform uses the **Groq API to access an LLM** for analyzing candidate skills and resume evidence.

The LLM evaluates each required skill and determines its status and proficiency.

## Skill Status

### Explicit

The skill is directly mentioned or clearly demonstrated in the candidate profile.

Example:

```text
Python is listed in the candidate's skills.
```

### Inferred

The skill is reasonably inferred from projects or experience.

Example:

```text
The candidate worked on an AI project,
suggesting some exposure to Machine Learning.
```

### Missing

There is insufficient evidence that the candidate possesses the skill.

Example:

```text
No mention or supporting evidence of Docker.
```

---

# 10. Skill Proficiency Analysis

The LLM categorizes the candidate's skill level as:

### Basic

Limited exposure, coursework, or simple project usage.

### Intermediate

Meaningful practical or project-level implementation.

### Expert

Strong professional/project experience or advanced demonstrated expertise.

The analysis can also return:

* Confidence
* Evidence
* Candidate level
* Required level
* Level match

Example:

```json
{
  "skill": "Python",
  "status": "explicit",
  "level": "Intermediate",
  "confidence": 0.8,
  "evidence": "Python is listed in skills and used in projects."
}
```

This makes the matching process more explainable than simple keyword matching.

---

# 11. Hiring Score

The candidate score uses the following weighting:

```text
Skills       = 80%
Experience   = 20%
```

The overall score is calculated as:

```text
Final Score =
    (Skill Score × 0.80)
  + (Experience Score × 0.20)
```

Skills have the higher weight because technical suitability is the primary factor in the candidate matching process.

Experience contributes the remaining 20%.

---

# 12. Skill Gap Analysis

For every selected candidate and job, the system identifies whether the candidate satisfies each required skill.

### Matched Skill

The candidate has the required skill at the required level.

Example:

```text
Required: Python → Intermediate
Candidate: Python → Intermediate

Result: Match
```

### Level Gap

The candidate has the skill but below the required level.

Example:

```text
Required: Python → Expert
Candidate: Python → Intermediate

Result: Level Gap
```

### Missing Skill

There is no sufficient evidence of the required skill.

Example:

```text
Required: Docker → Basic
Candidate: Docker → Missing

Result: Missing Skill
```

The skill-gap analysis also provides supporting evidence and confidence where applicable.

---

# 13. Tech Stack

## Backend

* Python
* FastAPI
* Uvicorn
* Pydantic

## Database

* SQLite
* SQLAlchemy

## Resume Processing

* PDF/DOCX parsing utilities

## NLP / Extraction

* spaCy
* Rule/pattern-based extraction

## AI / LLM

* Groq API
* LLM-based skill and evidence analysis

## Frontend

* HTML
* CSS
* JavaScript

---

# 14. Project Structure

```text
AI-Recruitment-Copilot/
│
├── app/
│   ├── main.py
│   ├── database.py
│   │
│   ├── routes/
│   │   ├── upload.py
│   │   ├── candidate.py
│   │   ├── job.py
│   │   └── matching.py
│   │
│   ├── services/
│   │   ├── parser.py
│   │   ├── extractor.py
│   │   └── ...
│   │
│   ├── models/
│   └── schemas/
│
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── style.css
│
├── uploads/
├── extracted_data/
├── .env
├── requirements.txt
└── README.md
```

---

# 15. Key Challenges

## Milestone 1

* Different resume layouts and formatting
* Incorrect name extraction
* Missing candidate information
* Resume parsing inconsistencies
* Database data-type issues
* Maintaining accuracy across different resume structures

## Milestone 2

* AI response-format inconsistencies
* Groq API quota/rate-limit issues
* Distinguishing explicit skills from inferred skills
* Determining Basic/Intermediate/Expert proficiency
* Handling missing skills
* Handling skills that exist but are below the required level
* Designing a meaningful candidate scoring system

---

# 16. Current Status

### ✅ Milestone 1 — Completed

**Resume Parsing & Candidate Profiling**

Implemented:

* Resume upload
* PDF/DOCX processing
* Candidate information extraction
* Structured candidate profiles
* Database storage
* Candidate APIs
* Frontend candidate display

### ✅ Milestone 2 — Completed

**Candidate Matching & Skill-Gap Analysis**

Implemented:

* Job requirements
* Required experience
* Required skills
* Skill proficiency levels
* Candidate-job matching
* Groq + LLM skill analysis
* Basic/Intermediate/Expert classification
* Explicit/Inferred/Missing status
* Hiring score
* Candidate ranking
* Skill-gap analysis

---

# 17. Future Scope

Possible future improvements include:

* Automated interview scheduling
* Advanced candidate recommendation
* Recruiter analytics dashboard
* Interview feedback analysis
* Email/notification automation
* Improved semantic resume understanding
* Advanced AI-assisted recruitment workflows

---

## Project Status

**Milestones 1 & 2 Completed**

The current core pipeline is:

```text
Resume
   ↓
Candidate Profile
   ↓
Job Requirements
   ↓
AI Skill Analysis
   ↓
Candidate Matching
   ↓
Hiring Score
   ↓
Candidate Ranking
   ↓
Skill Gap Analysis
```


