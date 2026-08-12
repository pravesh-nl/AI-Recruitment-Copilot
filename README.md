
# AI Recruitment & Talent Management Copilot


python -m venv venv
.\venv\Scripts\Activate.ps1
cd your_project_folder

python -m venv venv

venv\Scripts\activate

python -m pip install --upgrade pip

## Milestone 1: Resume Parsing & Candidate Profiling
Install all required packages::

FastAPI → Backend API
Uvicorn → Runs the API
python-multipart → Upload PDF/DOCX files
PyPDF + pdfplumber → Extract text from PDFs
python-docx → Read Word documents
spaCy → Process and analyze extracted text
Pandas → Store and analyze structured data
SQLAlchemy → Save results in a database
Streamlit → Build the frontend interface
python-dotenv → Securely manage API keys and configuration

### What is AI Recruitment Copilot?

AI Recruitment Copilot is an AI-based recruitment system that automatically reads resumes and creates structured candidate profiles.

Instead of HR manually reading every resume, the system extracts important details like:

* Name
* Email
* Phone Number
* Skills
* Education
* Experience
* Projects
* Certifications

and stores them in the database.

This saves time and improves the recruitment process.

---

# 2. Problem Statement

Companies receive hundreds of resumes.

Reading each resume manually is:

* Time consuming
* Error prone
* Repetitive

Our system automates this process.

---

# 3. Objective

Our goal is to

* Upload resumes
* Parse them automatically
* Extract useful information
* Store candidate profiles
* Display everything in an ATS-like dashboard

---

# 4. Technology Stack

## Frontend

Streamlit

Why?

Because it allows us to quickly build beautiful dashboards using only Python.

---

## Backend

FastAPI

Why?

Because it is

* Fast
* Lightweight
* Easy to build REST APIs
* Automatically generates API documentation

---

## Database

SQLite

Why?

* Lightweight
* No installation required
* Perfect for small projects

---

## ORM

SQLAlchemy

Why?

Instead of writing SQL queries manually,

we use Python objects.

Example

Instead of

```sql
SELECT * FROM candidate;
```

we write

```python
db.query(Candidate).all()
```

Much easier.

---

## Resume Parsing Libraries

### pdfplumber

Reads text from PDF resumes.

---

### python-docx

Reads Word (.docx) resumes.

---

### spaCy

NLP library.

Used to identify

* skills
* education
* experience
* names

from resume text.

---

## Other Libraries

### JSON

Stores lists like

Skills

Instead of

```
Python
SQL
Machine Learning
```

they are stored as

```json
["Python","SQL","Machine Learning"]
```

---

### Pandas

Displays candidate table.

---

### Requests

Connects Streamlit with FastAPI.

Example

```python
requests.get("/stats")
```

gets dashboard statistics.

---

# 5. Project Structure

```
AI-Recruitment-Copilot

│

├── app
│
│   ├── main.py
│
│   ├── database.py
│
│   ├── models
│
│   ├── routes
│
│   ├── services
│
│   ├── schemas
│
│   ├── utils
│
│   └── extracted_data

│

├── uploads

├── streamlit_app.py

├── requirements.txt

└── README.md
```

---

# 6. Explain Every File

---

# main.py

This is the entry point of FastAPI.

It

* starts FastAPI
* connects routes
* starts backend server

Without this file,

backend won't run.

---

# database.py

Creates connection with SQLite database.

Contains

```python
engine
```

SessionLocal

Base

These are required by SQLAlchemy.

---

# models/

Contains database tables.

Example

Candidate

UploadHistory

Each class represents one SQL table.

---

# Candidate Model

Stores

* Name
* Email
* Phone
* Skills
* Education
* Experience
* Projects
* Certifications

---

# UploadHistory Model

Stores upload information like

* uploaded file
* upload time

Used for Resume Processed count.

---

# routes/

Contains APIs.

There are mainly two route files.

---

## upload.py

Handles

POST /upload

Flow

Upload Resume

↓

Save Resume

↓

Parse Resume

↓

Extract Information

↓

Save Candidate

↓

Return Success

---

## candidate.py

Contains APIs

GET /candidates

Returns all candidates.

---

GET /candidate/{id}

Returns one candidate.

---

GET /stats

Returns

Resume Processed

Profiles Created

Parsing Accuracy

---

# services/

Contains actual business logic.

---

parser.py

Reads resume.

Uses

pdfplumber

python-docx

Returns plain text.

---

extractor.py

Uses NLP.

Extracts

Name

Email

Phone

Skills

Education

Experience

Projects

Certifications

Returns structured dictionary.

---

# schemas/

Contains request and response formats.

Used for validation.

---

# utils/

Contains helper functions.

Makes project clean.

---

# uploads/

Stores uploaded resumes.

---

# extracted_data/

Stores parsed data.

Useful for debugging.

---

# streamlit_app.py

Frontend.

Creates dashboard.

Shows

Upload Resume

↓

Parsing Progress

↓

Statistics

↓

Extracted Information

↓

Recently Processed Candidates

---

# requirements.txt

Contains all required Python libraries.

When someone runs

```
pip install -r requirements.txt
```

all libraries are installed automatically.

---

# 7. Backend Workflow

```
User uploads Resume

↓

Streamlit sends POST request

↓

FastAPI receives Resume

↓

Resume saved in uploads/

↓

Parser reads Resume

↓

Extractor extracts information

↓

Candidate stored in SQLite

↓

Stats updated

↓

Dashboard refreshed
```

---

# 8. APIs

## POST

```
/upload
```

Purpose

Uploads resume.

---

## GET

```
/candidates
```

Returns all candidates.

---

## GET

```
/candidate/{id}
```

Returns one candidate.

---

## GET

```
/stats
```

Returns

```json
{
 "resume_processed":5,
 "profiles_created":5,
 "parsing_accuracy":95
}
```

---

# 9. Database Tables

Candidate

Contains

```
id

name

email

phone

skills

education

experience

projects

certifications
```

---

UploadHistory

Contains

```
id

filename

upload_time
```

---

# 10. Parsing Accuracy

We are using **Weighted Accuracy**.

Every field has a weight.

| Field          | Weight |
| -------------- | ------ |
| Name           | 20     |
| Email          | 20     |
| Phone          | 10     |
| Skills         | 20     |
| Education      | 15     |
| Experience     | 10     |
| Projects       | 3      |
| Certifications | 2      |

Maximum Score

```
100
```

Example

If parser extracts

Name

Email

Phone

Skills

Education

Experience

Projects

Missing Certifications

Score

```
20+20+10+20+15+10+3=98%
```

Dashboard shows average accuracy of all resumes.

---

# 11. Streamlit Dashboard Features

Upload Resume

↓

Animated Parsing Progress

↓

Dashboard Cards

* Resume Processed
* Parsing Accuracy
* Profiles Created

↓

Latest Candidate Information

↓

Recently Processed Candidates

↓

Expandable Candidate Profile

---

# 12. Why FastAPI?

* Faster than Flask
* Automatic API documentation
* Async support
* Better performance
* Easy integration with frontend

---

# 13. Why Streamlit?

* Pure Python
* No HTML required
* Beautiful UI
* Easy charts and tables
* Very fast development

---

# 14. Why SQLAlchemy?

Instead of SQL,

we use Python.

Example

Without SQLAlchemy

```sql
INSERT INTO Candidate ...
```

With SQLAlchemy

```python
db.add(candidate)
db.commit()
```

Cleaner and easier.

---

# 15. Why spaCy?

spaCy is an NLP library.

It understands language.

It helps identify

* Skills
* Education
* Experience
* Organizations
* Person Names

from resume text.

---

# 16. Current Features

* PDF upload
* DOCX upload
* Resume parsing
* Candidate profile creation
* SQLite database storage
* Parsing progress animation
* Weighted parsing accuracy
* ATS-style dashboard
* Expandable candidate profile
* Recently processed candidate list

---

# 17. Future Improvements (Milestone 2 & Beyond)

* Resume ranking using AI
* JD (Job Description) matching
* Candidate recommendation
* Resume scoring
* Skill-gap analysis
* AI chatbot for recruiters
* Email notifications
* Recruiter login
* Resume search and filters
* Export candidates to Excel/PDF

---

# 18. README.md (GitHub)

```markdown
# AI Recruitment Copilot

AI Recruitment Copilot is an AI-powered resume parsing system that automates candidate profiling for recruiters.

## Features

- Upload PDF and DOCX resumes
- Automatic resume parsing
- Candidate profile extraction
- SQLite database storage
- Weighted Parsing Accuracy
- Animated parsing progress
- ATS-style dashboard
- Expandable candidate profiles
- Recently processed candidates table

## Tech Stack

Frontend:
- Streamlit

Backend:
- FastAPI

Database:
- SQLite
- SQLAlchemy ORM

Resume Parsing:
- pdfplumber
- python-docx
- spaCy

Utilities:
- pandas
- requests

## APIs

POST /upload

GET /candidates

GET /candidate/{id}

GET /stats

## Installation

pip install -r requirements.txt

Run Backend

uvicorn app.main:app --reload

Run Frontend

streamlit run streamlit_app.py

## Project Workflow

Upload Resume

↓

Parse Resume

↓

Extract Candidate Details

↓

Store in SQLite

↓

Display Dashboard
```

---

------Milestone 2 — Job Posting & Candidate Matching----

Milestone 2 adds a job-based candidate matching system to AI Recruitment Copilot.

Features
Create job postings with:
Job title
Minimum experience
Required skills and proficiency levels
Store and retrieve created jobs through the backend.
Select a job and automatically rank available candidates.
Calculate a candidate match score based on skills and experience.
Display matching candidates with their match level.
View detailed skill-gap analysis showing:
Matched skills
Skill-level gaps
Missing skills
Experience gap
Skill-gap recommendations
Main Backend Components

File	Role
routes/jobs.py	               Job creation and job retrieval APIs
routes/matching.py	           Candidate matching and skill-gap APIs
models/job.py	               Job and job-skill database models
schemas.py	                   Request/response validation for jobs and matching
services/matching.py	       Matching-score and candidate-ranking logic

Main APIs 
POST /jobs
GET  /jobs
GET  /matching/job/{job_id}
GET  /matching/skill-gap/{job_id}/{candidate_id}

In short: Milestone 2 transforms the system from simply parsing resumes into an actual recruitment assistant that creates jobs, evaluates candidates, ranks them, and identifies skill gaps.