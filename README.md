README — Milestones 1 & 2
AI-powered recruitment platform for resume parsing, candidate profiling, job matching, AI skill analysis, ranking and skill-gap identification.
1. Project Overview
The platform automates key recruitment activities by converting unstructured resumes into structured candidate profiles and comparing those profiles against job requirements. Milestone 1 establishes the candidate-data foundation, while Milestone 2 performs candidate matching and explainable skill-gap analysis.
2. Problem Statement
Manual resume screening is time-consuming because resumes have different formats and layouts. Recruiters must extract candidate information, compare skills with job requirements, evaluate experience and identify missing skills. This project automates these steps and provides a consistent, evidence-based candidate evaluation workflow.
3. Solution Workflow
Resume Upload → PDF/DOCX file is submitted through the frontend.
Resume Parsing → FastAPI receives the file and the parser extracts usable text.
Candidate Extraction → Candidate name, contact information, skills, education, location and experience are extracted where available.
Profile Storage → Structured candidate information is validated and stored in the database.
Job Management → Recruiter creates/selects a job containing required experience and skills with proficiency levels.
AI Skill Analysis → Groq + LLM analyzes candidate evidence for each required skill.
Matching → Candidate skills and experience are compared with job requirements.
Scoring & Ranking → Candidates receive a hiring score and are ranked.
Skill Gap → Missing or below-required skills are identified with evidence and confidence.
4. Milestone 1 — Resume Parsing & Candidate Profiling
Milestone 1 converts unstructured resumes into reusable candidate profiles.
Resume upload and processing
PDF/DOCX text extraction
Candidate information extraction
Skill extraction and normalization
Education, location and experience extraction where available
Candidate profile creation and database storage
Candidate retrieval and statistics APIs
Frontend display of processed candidates
5. Milestone 1 — Backend Components
Component
Purpose
app/main.py
FastAPI application entry point and route registration.
app/database.py
Database connection and session management.
app/routes/upload.py
Receives resume uploads and starts processing.
app/routes/candidate.py
Provides candidate retrieval APIs.
app/services/parser.py
Handles resume/document parsing.
app/services/extractor.py
Extracts candidate fields from parsed content.
app/models/candidate.py
Defines the candidate database model.
app/models/upload_history.py
Tracks upload/processing information.
app/schemas/
Defines structured API request/response data.

6. Milestone 2 — Candidate Matching & Skill-Gap Analysis
Milestone 2 uses the structured profiles from Milestone 1 and compares them against selected job requirements.
Job creation and requirements
Required experience and skill levels
Candidate-job matching
Candidate ranking
Skill-level comparison
Groq/LLM-based skill analysis
Hiring score calculation
Skill-gap analysis
7. Groq + LLM Skill Analysis
The Groq API provides access to an LLM that analyzes resume evidence against each required skill. The system does not simply check whether a keyword exists; it evaluates evidence and proficiency.
Explicit — skill is directly mentioned or clearly demonstrated.
Inferred — skill is reasonably inferred from project or experience evidence.
Missing — there is insufficient evidence of the skill.
Proficiency levels:
Basic — limited exposure, coursework or simple project usage.
Intermediate — meaningful practical/project implementation.
Expert — strong professional/project experience or advanced demonstrated expertise.
Each analysis can include confidence and supporting evidence, making the result more explainable.
8. Hiring Score
The implemented weighting gives greater importance to technical skill suitability:
Final Score = (Skill Score × 0.80) + (Experience Score × 0.20)
Skills contribute 80% and experience contributes 20% to the overall hiring score.
9. Skill Gap Analysis
Matched Skill — candidate meets the required proficiency.
Level Gap — candidate has the skill but below the required proficiency.
Missing Skill — no sufficient evidence of the required skill.
Evidence and confidence provide context for AI-based decisions.
10. Tech Stack
Layer
Technology
Language
Python
Backend
FastAPI, Uvicorn
Database
SQLite, SQLAlchemy
Validation
Pydantic
Resume Processing
PDF/DOCX parsing utilities
NLP / Extraction
spaCy + rule/pattern-based extraction
AI / LLM
Groq API + LLM
Frontend
HTML, CSS, JavaScript

11. Project Structure
AI-Recruitment-Copilot/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── routes/
│   │   ├── upload.py
│   │   ├── candidate.py
│   │   ├── job.py
│   │   └── matching.py
│   ├── services/
│   │   ├── parser.py
│   │   ├── extractor.py
│   │   └── ...
│   ├── models/
│   └── schemas/
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── style.css
├── uploads/
├── extracted_data/
├── .env
├── requirements.txt
└── README.md
12. Key Challenges
Different resume layouts and formatting.
Incorrect name extraction from headings/labels or unrelated prominent text.
Missing candidate information.
AI response-format inconsistencies.
API quota/rate-limit handling.
Distinguishing explicit skills from reasonable inference.
Assigning Basic/Intermediate/Expert proficiency from evidence.
Separating missing skills from skills that are present but below the required level.
13. Current Status
Milestone 1 — Resume Parsing & Candidate Profiling: Completed.
Milestone 2 — Candidate Matching & Skill-Gap Analysis: Completed.
Core workflow: Resume → Candidate Profile → Job → AI Skill Analysis → Matching → Ranking → Skill Gap.
14. Future Scope
Automated interview scheduling
Advanced candidate recommendation
Recruiter analytics
Interview feedback analysis
Email/notification automation
Improved semantic resume understanding
Advanced AI-assisted recruitment workflows
Project Status: Milestones 1 & 2 Completed
