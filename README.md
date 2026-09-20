<<<<<<< HEAD
# AI Driven Smart Hiring Platform With Candidate Matching Copilot

An end-to-end AI-assisted recruitment platform that helps recruiters move from **resume processing and candidate profiling to job matching, AI interviewing, preliminary voice screening, analytics, and final recruiter-controlled hiring decisions** in one application.

> **Core principle:** AI assists the recruiter; it does not independently make the final hiring decision.

---

## 🚀 Live Demo

| Component | URL |
|---|---|
| **Frontend** | https://ai-recruitment-copilot-gz9x.onrender.com |
| **Backend API** | https://ai-driven-smart-hiring-platform-with-2q4r.onrender.com |
| **API Documentation** | https://ai-driven-smart-hiring-platform-with-2q4r.onrender.com/docs |

---

## 📌 Project Overview

Recruitment involves several repetitive and disconnected activities such as resume screening, candidate-job comparison, interviews, screening, and final evaluation. This project brings those activities into a single recruiter-facing platform.

The system can:

- Parse PDF/DOCX resumes and create structured candidate profiles.
- Manage jobs and role requirements.
- Define required skill proficiency as **Basic, Intermediate, or Advanced**.
- Perform deterministic ATS candidate-job matching.
- Identify skill gaps for a selected candidate and job.
- Conduct a deeper **text-based AI Interview**.
- Conduct a **preliminary Voice Screening** using the browser Web Speech API.
- Provide AI-assisted evaluation while avoiding automatic hiring decisions.
- Display real recruitment analytics through a dashboard.
- Record recruiter decisions such as **Hired, Not Selected, In Progress, or Pending**.

---

## 🎯 Problem Statement

Recruiters often need to manually review resumes, compare candidates against job requirements, conduct interviews, perform initial screening, and then consolidate multiple evaluation results before making a hiring decision.

The project addresses this by providing a centralized platform that combines **candidate profiling, job-specific matching, interview evaluation, preliminary voice screening, analytics, and recruiter-controlled decision making**.

---

## ✨ Key Features

### 1. Resume Upload & Candidate Profiling

- PDF/DOCX resume processing.
- Extraction of name, contact information, location, education, experience, and skills.
- spaCy-based NLP for structured extraction.
- Safe handling of missing or ambiguous names.
- `name_source` records the provenance of an extracted name when available.

When a valid candidate name cannot be determined, the system uses **“Name not provided”** rather than incorrectly treating a location, company, college, or skill as the person's name.

### 2. Job Management

Recruiters can create job requirements including:

- Job title and description
- Required skills
- Minimum experience
- Skill proficiency requirements

Each required skill can be assigned:

- **Basic**
- **Intermediate**
- **Advanced**

These are **required skill proficiency levels**, not overall candidate match levels.

### 3. ATS / Candidate-Job Matching

The platform provides deterministic candidate-job matching for more consistent and explainable results.

**Overall match tiers:**

| Tier | Score |
|---|---:|
| Excellent | 85–100% |
| Strong | 70–84% |
| Moderate | 50–69% |
| Low | Below 50% |

The platform also supports **skill-gap analysis** for a selected candidate and job.

ATS results are decision-support evidence and do not automatically hire or reject candidates.

### 4. AI Interview Assistant

The AI Interview is the **deeper technical and behavioral evaluation layer**.

- Context-aware question generation.
- Maximum **7 questions** per interview.
- Progress shown as **Question X of 7**.
- Evaluation based on the candidate's actual submitted answers.
- Empty/meaningless responses are not treated as valid evidence.
- Final result includes the existing interview assessment and:
  - **Recommended**
  - **Not Recommended**
  - **Pending / Not Evaluated**

### 5. Preliminary Voice Screening

Voice Screening is intentionally separate from the deeper AI Interview.

It focuses on preliminary indicators such as:

- Communication
- Clarity
- Fluency
- Confidence
- Professionalism
- Basic domain familiarity
- Basic teamwork/leadership indicators

Technical features:

- Browser `SpeechRecognition` / `webkitSpeechRecognition`
- Browser `SpeechSynthesis`
- Maximum **5 questions**
- Progress shown as **Question X of 5**
- Manual **Submit Answer** control
- Natural pauses do not automatically submit the answer
- Actual submitted transcripts are evaluated and persisted

**Voice Screening result:**

- **Screened**
- **Not Screened**
- **Pending / Not Evaluated**

### 6. Answer Naturalness Insight

Voice Screening can also provide a cautious observation such as:

- Natural
- Possibly Scripted
- Highly Scripted / Potentially AI-Assisted

This is an **additional observation, not a definitive AI detector**, and does not replace the main Screened / Not Screened result.

### 7. Recruiter Hiring Decision

The recruiter reviews the available evidence and makes the final decision.

Possible states:

- **Hired**
- **Not Selected**
- **In Progress**
- **Pending / Not Evaluated**

No ATS score, AI Interview result, or Voice Screening result automatically becomes a hiring decision.

### 8. Recruiter Dashboard

The dashboard provides real project analytics including:

- Candidate and job counts
- Interview activity
- Voice Screening activity
- Candidate skill distribution
- ATS matching analytics
- AI Interview analytics
- Voice Screening insights
- Evaluation comparison
- Candidate hiring status

Dashboard values are derived from application data rather than fabricated HR metrics.

---

## 🧩 Evaluation Layers

The application deliberately separates the different evaluation stages:

| Layer | Purpose | Result |
|---|---|---|
| **ATS Match** | Job-specific candidate fit | Excellent / Strong / Moderate / Low |
| **AI Interview** | Deeper technical/behavioral evaluation | Recommended / Not Recommended / Pending |
| **Voice Screening** | Preliminary spoken screening | Screened / Not Screened / Pending |
| **Recruiter Decision** | Final human decision | Hired / Not Selected / In Progress / Pending |

This separation prevents one evaluation from incorrectly replacing another.

---

## 🏗️ System Architecture

```text
                         USER / RECRUITER
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                             │
│   HTML + CSS + JavaScript + Chart.js + Web Speech API     │
└─────────────────────────────┬───────────────────────────────┘
                              │ REST APIs
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                        │
│                                                             │
│ Candidates │ Jobs │ ATS │ AI Interview │ Voice Screening   │
│ Dashboard │ Hiring Decision │ Resume Upload                │
└───────────────────────┬───────────────────┬─────────────────┘
                        │                   │
                        ▼                   ▼
             ┌─────────────────┐   ┌────────────────────────┐
             │ SQLite +        │   │ AI / NLP               │
             │ SQLAlchemy      │   │                        │
             │                 │   │ Groq LLM               │
             │ Candidates      │   │ spaCy                   │
             │ Jobs            │   │ PDF/DOCX extraction     │
             │ Sessions        │   │ AI evaluation           │
             │ Hiring status   │   └────────────────────────┘
             └─────────────────┘
```
=======
I Driven Smart Hiring Platform With Candidate Matching Copilot
>>>>>>> e20304f62eecb18c9fafaf92620b322301c15653

An end-to-end AI-assisted recruitment platform that helps recruiters move from resume processing and candidate profiling to job matching, AI interviewing, preliminary voice screening, analytics, and final recruiter-controlled hiring decisions in one application.

<<<<<<< HEAD
## 🛠️ Technology Stack

### Frontend

- HTML5
- CSS3
- Vanilla JavaScript
- Chart.js
- Web Speech API

### Backend

- Python
- FastAPI
- SQLAlchemy
- REST APIs

### Database

- SQLite

### AI / NLP

- Groq API
- Current model: `openai/gpt-oss-120b`
- spaCy
- PDF/DOCX extraction

### Deployment

- Git
- GitHub
- Render
=======
Core principle: AI assists the recruiter; it does not independently make the final hiring decision.

🚀 Live Demo

Component

URL

Frontend

https://ai-recruitment-copilot-gz9x.onrender.com
>>>>>>> e20304f62eecb18c9fafaf92620b322301c15653

Backend API

<<<<<<< HEAD
## 📂 Project Structure

```text
=======
https://ai-driven-smart-hiring-platform-with-2q4r.onrender.com

API Documentation

https://ai-driven-smart-hiring-platform-with-2q4r.onrender.com/docs

📌 Project Overview

Recruitment involves several repetitive and disconnected activities such as resume screening, candidate-job comparison, interviews, screening, and final evaluation. This project brings those activities into a single recruiter-facing platform.

The system can:

Parse PDF/DOCX resumes and create structured candidate profiles.

Manage jobs and role requirements.

Define required skill proficiency as Basic, Intermediate, or Advanced.

Perform deterministic ATS candidate-job matching.

Identify skill gaps for a selected candidate and job.

Conduct a deeper text-based AI Interview.

Conduct a preliminary Voice Screening using the browser Web Speech API.

Provide AI-assisted evaluation while avoiding automatic hiring decisions.

Display real recruitment analytics through a dashboard.

Record recruiter decisions such as Hired, Not Selected, In Progress, or Pending.

🎯 Problem Statement

Recruiters often need to manually review resumes, compare candidates against job requirements, conduct interviews, perform initial screening, and then consolidate multiple evaluation results before making a hiring decision.

The project addresses this by providing a centralized platform that combines candidate profiling, job-specific matching, interview evaluation, preliminary voice screening, analytics, and recruiter-controlled decision making.

✨ Key Features

1. Resume Upload & Candidate Profiling

PDF/DOCX resume processing.

Extraction of name, contact information, location, education, experience, and skills.

spaCy-based NLP for structured extraction.

Safe handling of missing or ambiguous names.

name_source records the provenance of an extracted name when available.

When a valid candidate name cannot be determined, the system uses “Name not provided” rather than incorrectly treating a location, company, college, or skill as the person's name.

2. Job Management

Recruiters can create job requirements including:

Job title and description

Required skills

Minimum experience

Skill proficiency requirements

Each required skill can be assigned:

Basic

Intermediate

Advanced

These are required skill proficiency levels, not overall candidate match levels.

3. ATS / Candidate-Job Matching

The platform provides deterministic candidate-job matching for more consistent and explainable results.

Overall match tiers:

Tier

Score

Excellent

85–100%

Strong

70–84%

Moderate

50–69%

Low

Below 50%

The platform also supports skill-gap analysis for a selected candidate and job.

ATS results are decision-support evidence and do not automatically hire or reject candidates.

4. AI Interview Assistant

The AI Interview is the deeper technical and behavioral evaluation layer.

Context-aware question generation.

Maximum 7 questions per interview.

Progress shown as Question X of 7.

Evaluation based on the candidate's actual submitted answers.

Empty/meaningless responses are not treated as valid evidence.

Final result includes the existing interview assessment and:

Recommended

Not Recommended

Pending / Not Evaluated

5. Preliminary Voice Screening

Voice Screening is intentionally separate from the deeper AI Interview.

It focuses on preliminary indicators such as:

Communication

Clarity

Fluency

Confidence

Professionalism

Basic domain familiarity

Basic teamwork/leadership indicators

Technical features:

Browser SpeechRecognition / webkitSpeechRecognition

Browser SpeechSynthesis

Maximum 5 questions

Progress shown as Question X of 5

Manual Submit Answer control

Natural pauses do not automatically submit the answer

Actual submitted transcripts are evaluated and persisted

Voice Screening result:

Screened

Not Screened

Pending / Not Evaluated

6. Answer Naturalness Insight

Voice Screening can also provide a cautious observation such as:

Natural

Possibly Scripted

Highly Scripted / Potentially AI-Assisted

This is an additional observation, not a definitive AI detector, and does not replace the main Screened / Not Screened result.

7. Recruiter Hiring Decision

The recruiter reviews the available evidence and makes the final decision.

Possible states:

Hired

Not Selected

In Progress

Pending / Not Evaluated

No ATS score, AI Interview result, or Voice Screening result automatically becomes a hiring decision.

8. Recruiter Dashboard

The dashboard provides real project analytics including:

Candidate and job counts

Interview activity

Voice Screening activity

Candidate skill distribution

ATS matching analytics

AI Interview analytics

Voice Screening insights

Evaluation comparison

Candidate hiring status

Dashboard values are derived from application data rather than fabricated HR metrics.

🧩 Evaluation Layers

The application deliberately separates the different evaluation stages:

Layer

Purpose

Result

ATS Match

Job-specific candidate fit

Excellent / Strong / Moderate / Low

AI Interview

Deeper technical/behavioral evaluation

Recommended / Not Recommended / Pending

Voice Screening

Preliminary spoken screening

Screened / Not Screened / Pending

Recruiter Decision

Final human decision

Hired / Not Selected / In Progress / Pending

This separation prevents one evaluation from incorrectly replacing another.

🏗️ System Architecture

                         USER / RECRUITER
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                             │
│   HTML + CSS + JavaScript + Chart.js + Web Speech API     │
└─────────────────────────────┬───────────────────────────────┘
                              │ REST APIs
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                        │
│                                                             │
│ Candidates │ Jobs │ ATS │ AI Interview │ Voice Screening   │
│ Dashboard │ Hiring Decision │ Resume Upload                │
└───────────────────────┬───────────────────┬─────────────────┘
                        │                   │
                        ▼                   ▼
             ┌─────────────────┐   ┌────────────────────────┐
             │ SQLite +        │   │ AI / NLP               │
             │ SQLAlchemy      │   │                        │
             │                 │   │ Groq LLM               │
             │ Candidates      │   │ spaCy                   │
             │ Jobs            │   │ PDF/DOCX extraction     │
             │ Sessions        │   │ AI evaluation           │
             │ Hiring status   │   └────────────────────────┘
             └─────────────────┘

🛠️ Technology Stack

Frontend

HTML5

CSS3

Vanilla JavaScript

Chart.js

Web Speech API

Backend

Python

FastAPI

SQLAlchemy

REST APIs

Database

SQLite

AI / NLP

Groq API

Current model: openai/gpt-oss-120b

spaCy

PDF/DOCX extraction

Deployment

Git

GitHub

Render

📂 Project Structure

>>>>>>> e20304f62eecb18c9fafaf92620b322301c15653
AI Driven Smart Hiring Platform With Canditate Matching Copilot/
│
├── app/
│   ├── models/              # Database entities/models
│   ├── routes/              # FastAPI API endpoints
│   ├── schemas/             # Request/response validation
│   ├── services/            # Business logic, AI and NLP services
│   ├── database.py          # Database configuration
│   └── main.py              # FastAPI application entry point
│
├── frontend/
│   ├── index.html           # Main application UI
│   ├── script.js            # Frontend logic and API integration
│   └── style.css            # Frontend styling
│
├── requirements.txt
├── recruitment.db           # Local SQLite database
└── README.md

🔄 Main Workflow

<<<<<<< HEAD
## 🔄 Main Workflow

### Resume → Candidate

```text
=======
Resume → Candidate

>>>>>>> e20304f62eecb18c9fafaf92620b322301c15653
Resume Upload
     ↓
PDF/DOCX Extraction
     ↓
NLP / Structured Parsing
     ↓
Candidate Profile
     ↓
SQLite Persistence
<<<<<<< HEAD
```

### Candidate → Job Matching

```text
=======

Candidate → Job Matching

>>>>>>> e20304f62eecb18c9fafaf92620b322301c15653
Candidate Profile + Job Requirements
                ↓
       Deterministic ATS Matching
                ↓
         Match Score / Tier
                ↓
           Skill Gap Analysis
<<<<<<< HEAD
```

### AI Interview

```text
=======

AI Interview

>>>>>>> e20304f62eecb18c9fafaf92620b322301c15653
Candidate + Job Context
        ↓
AI Question Generation
        ↓
Candidate Answers
        ↓
Maximum 7 Questions
        ↓
Final Assessment
        ↓
Recommended / Not Recommended
<<<<<<< HEAD
```

### Voice Screening

```text
=======

Voice Screening

>>>>>>> e20304f62eecb18c9fafaf92620b322301c15653
Candidate + Job Context
        ↓
AI Screening Question
        ↓
SpeechSynthesis
        ↓
Candidate Speaks
        ↓
SpeechRecognition
        ↓
Transcript
        ↓
Candidate presses Submit Answer
        ↓
Maximum 5 Questions
        ↓
Preliminary Assessment
        ↓
Screened / Not Screened
<<<<<<< HEAD
```

### Final Recruiter Decision

```text
=======

Final Recruiter Decision

>>>>>>> e20304f62eecb18c9fafaf92620b322301c15653
Resume/Profile
     ↓
ATS Match + Skill Gap
     ↓
AI Interview (if completed)
     ↓
Voice Screening (if completed)
     ↓
Recruiter Review
     ↓
Hired / Not Selected / In Progress / Pending
<<<<<<< HEAD
```

---

## ⚙️ Installation & Local Setup

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd "AI Driven Smart Hiring Platform With Canditate Matching Copilot"
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

If the current resume extraction setup uses the large spaCy English model:

```bash
python -m spacy download en_core_web_lg
```

### 4. Configure the Groq API key

Set the environment variable used by the project, for example:

```env
GROQ_API_KEY=your_key_here
```

**Never commit real API keys or `.env` secrets to GitHub.**

### 5. Start the backend

```bash
uvicorn app.main:app --reload
```

Local backend:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

### 6. Start the frontend

Serve the `frontend/` directory using your preferred local static server.

For local development, ensure the frontend API configuration points to the intended backend.

---

## 🌐 Production Deployment

The application is deployed as a GitHub-connected Render service.

### Backend start command

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Production API base URL

```text
https://ai-driven-smart-hiring-platform-with-2q4r.onrender.com
```

The production frontend must use the deployed API URL rather than `localhost` or `127.0.0.1`.

### Deployment flow

```text
=======

⚙️ Installation & Local Setup

1. Clone the repository

git clone <YOUR_GITHUB_REPOSITORY_URL>
cd "AI Driven Smart Hiring Platform With Canditate Matching Copilot"

2. Create a virtual environment

Windows PowerShell:

python -m venv venv
venv\Scripts\Activate.ps1

3. Install dependencies

pip install -r requirements.txt

If the current resume extraction setup uses the large spaCy English model:

python -m spacy download en_core_web_lg

4. Configure the Groq API key

Set the environment variable used by the project, for example:

GROQ_API_KEY=your_key_here

Never commit real API keys or .env secrets to GitHub.

5. Start the backend

uvicorn app.main:app --reload

Local backend:

http://127.0.0.1:8000

Swagger:

http://127.0.0.1:8000/docs

6. Start the frontend

Serve the frontend/ directory using your preferred local static server.

For local development, ensure the frontend API configuration points to the intended backend.

🌐 Production Deployment

The application is deployed as a GitHub-connected Render service.

Backend start command

uvicorn app.main:app --host 0.0.0.0 --port $PORT

Production API base URL

https://ai-driven-smart-hiring-platform-with-2q4r.onrender.com

The production frontend must use the deployed API URL rather than localhost or 127.0.0.1.

Deployment flow

>>>>>>> e20304f62eecb18c9fafaf92620b322301c15653
VS Code
  ↓
git add .
  ↓
git commit
  ↓
git push
  ↓
GitHub
  ↓
Render Build
  ↓
Render Deploy
  ↓
Live Application
<<<<<<< HEAD
```

---

## 🧪 Testing Checklist

Before deployment, verify:

- [ ] Resume upload works.
- [ ] PDF/DOCX extraction works.
- [ ] Missing names are handled safely.
- [ ] Candidate profile persists correctly.
- [ ] Job creation works.
- [ ] Basic/Intermediate/Advanced skill levels work.
- [ ] ATS matching returns the correct job-specific result.
- [ ] Skill Gap Analysis works.
- [ ] AI Interview supports a maximum of 7 questions.
- [ ] AI Interview shows Recommended/Not Recommended/Pending.
- [ ] Empty interview answers do not receive free positive marks.
- [ ] Voice Screening supports a maximum of 5 questions.
- [ ] Natural pauses do not automatically submit voice answers.
- [ ] Save & Evaluate works with submitted answers.
- [ ] Voice Screening shows Screened/Not Screened/Pending.
- [ ] Dashboard loads real project data.
- [ ] Recruiter Hiring Decision updates correctly.
- [ ] Production frontend does not call `localhost:8000`.
- [ ] Groq failures are handled gracefully.

---

## 🧱 Four Development Milestones

### Milestone 1 — Resume Parsing & Candidate Profiling

Established the candidate foundation by extracting structured information from uploaded resumes and creating reusable candidate profiles.

### Milestone 2 — Job Management & ATS Matching

Connected candidates to role requirements, introduced **Basic / Intermediate / Advanced** skill proficiency levels, deterministic ATS matching, match tiers, and skill-gap analysis.

### Milestone 3 — AI Interview Assistant

Introduced a deeper text-based technical/behavioral interview with contextual questions, stored assessments, and recruiter-facing recommendations.

### Milestone 4 — Voice Screening, Dashboard & Hiring Decision

Added preliminary browser-based voice screening, transcript-based assessment, dashboard analytics, and recruiter-controlled final hiring status.

---

## 🔐 Design & Reliability Principles

### Human-in-the-loop

AI provides supporting evidence; the recruiter controls the final hiring decision.

### Deterministic core matching

ATS matching remains deterministic and job-specific rather than relying on an LLM for every match calculation.

### Independent evaluation layers

ATS, AI Interview, Voice Screening, and Recruiter Hiring Decision remain separate concepts.

### Real data

Dashboard and candidate status information are based on actual application records rather than fabricated recruitment metrics.

### Graceful AI fallback

AI-service failures should result in user-friendly temporary-unavailability behavior rather than fabricated scores or raw server failures.

---

## 🔮 Future Scope

Potential future extensions include:

- Richer candidate search and filtering
- Interview scheduling and calendar integration
- Role-specific assessment templates
- Expanded recruiter collaboration
- Stronger production data persistence
- Additional audit and analytics capabilities

---

## 👤 Author

**Pravesh Nirmal**  
Individual Project · Artificial Intelligence (AI)  
Infosys Springboard Virtual Internship 7.0

---

## 📄 Project Note
=======

🧪 Testing Checklist

Before deployment, verify:

Resume upload works.

PDF/DOCX extraction works.

Missing names are handled safely.

Candidate profile persists correctly.

Job creation works.

Basic/Intermediate/Advanced skill levels work.

ATS matching returns the correct job-specific result.

Skill Gap Analysis works.

AI Interview supports a maximum of 7 questions.

AI Interview shows Recommended/Not Recommended/Pending.

Empty interview answers do not receive free positive marks.

Voice Screening supports a maximum of 5 questions.

Natural pauses do not automatically submit voice answers.

Save & Evaluate works with submitted answers.

Voice Screening shows Screened/Not Screened/Pending.

Dashboard loads real project data.

Recruiter Hiring Decision updates correctly.

Production frontend does not call localhost:8000.

Groq failures are handled gracefully.

🧱 Four Development Milestones

Milestone 1 — Resume Parsing & Candidate Profiling

Established the candidate foundation by extracting structured information from uploaded resumes and creating reusable candidate profiles.

Milestone 2 — Job Management & ATS Matching

Connected candidates to role requirements, introduced Basic / Intermediate / Advanced skill proficiency levels, deterministic ATS matching, match tiers, and skill-gap analysis.

Milestone 3 — AI Interview Assistant

Introduced a deeper text-based technical/behavioral interview with contextual questions, stored assessments, and recruiter-facing recommendations.

Milestone 4 — Voice Screening, Dashboard & Hiring Decision

Added preliminary browser-based voice screening, transcript-based assessment, dashboard analytics, and recruiter-controlled final hiring status.

🔐 Design & Reliability Principles

Human-in-the-loop

AI provides supporting evidence; the recruiter controls the final hiring decision.

Deterministic core matching

ATS matching remains deterministic and job-specific rather than relying on an LLM for every match calculation.

Independent evaluation layers

ATS, AI Interview, Voice Screening, and Recruiter Hiring Decision remain separate concepts.

Real data

Dashboard and candidate status information are based on actual application records rather than fabricated recruitment metrics.

Graceful AI fallback

AI-service failures should result in user-friendly temporary-unavailability behavior rather than fabricated scores or raw server failures.

🔮 Future Scope

Potential future extensions include:

Richer candidate search and filtering

Interview scheduling and calendar integration

Role-specific assessment templates

Expanded recruiter collaboration

Stronger production data persistence

Additional audit and analytics capabilities

👤 Author

Pravesh Nirmal
Individual Project · Artificial Intelligence (AI)
Infosys Springboard Virtual Internship 7.0

📄 Project Note
>>>>>>> e20304f62eecb18c9fafaf92620b322301c15653

This repository contains an academic/internship implementation of an AI-assisted recruitment decision-support platform. The project is intended to demonstrate full-stack engineering, NLP, AI integration, candidate matching, voice interaction, analytics, testing, and deployment.
