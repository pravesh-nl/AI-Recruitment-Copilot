# 🤖 AI Recruitment Copilot

uvicorn app.main:app --reload  
python -m streamlit run streamlit_app.py

An AI-powered Resume Parsing and Candidate Profiling System built using **FastAPI**, **Streamlit**, **spaCy**, and **SQLite**. The application automatically extracts key candidate information from PDF and DOCX resumes, stores it in a database, and displays the results through an interactive dashboard.

---

# 📌 Features

* 📄 Upload resumes in **PDF** and **DOCX** format
* 🤖 Automatic resume parsing
* 👤 Candidate profile generation
* 🧠 NLP-based information extraction using **spaCy**
* 💾 Store extracted data in SQLite
* 📊 Interactive Streamlit Dashboard
* 📈 Parsing Progress Indicator
* 🎯 Weighted Parsing Accuracy
* 📋 Candidate Management Dashboard
* 📑 Resume Upload History
* 🔍 Supports multiple resume formats

---

# 🛠 Tech Stack

## Frontend

* Streamlit

## Backend

* FastAPI

## Database

* SQLite
* SQLAlchemy ORM

## NLP

* spaCy (`en_core_web_lg`)
* PhraseMatcher

## File Parsing

* pypdf
* pdfplumber
* python-docx

## Other Libraries

* pandas
* requests
* json
* regex (re)

---

# 📂 Project Structure

```text
AI-Recruitment-Copilot/

│
├── app/
│   ├── main.py
│   ├── database.py
│   │
│   ├── models/
│   │      ├── candidate.py
│   │      └── upload_history.py
│   │
│   ├── routes/
│   │      ├── upload.py
│   │      └── candidate.py
│   │
│   └── services/
│          ├── parser.py
│          └── extractor.py
│
├── ui/
│      └── sidebar.py
│
├── uploads/
│
├── streamlit_app.py
├── recruitment.db
├── requirements.txt
└── README.md
```

---

# ⚙️ How It Works

```text
User Uploads Resume
          │
          ▼
FastAPI receives file
          │
          ▼
Resume saved in uploads/
          │
          ▼
parser.py extracts raw text
          │
          ▼
extractor.py extracts details
          │
          ▼
SQLite Database
          │
          ▼
Streamlit Dashboard
```

---

# 📋 Information Extracted

The system automatically extracts:

* Name
* Email
* Phone Number
* Skills
* Education
* Experience
* Projects
* Certifications

---

# 📁 Supported Resume Formats

* PDF (.pdf)
* Microsoft Word (.docx)

---

# 🧠 NLP Pipeline

The project uses **spaCy** with the `en_core_web_lg` language model.

Extraction techniques include:

* Named Entity Recognition (NER)
* Phrase Matching
* Regular Expressions
* Section Detection
* Rule-Based Parsing

---

# 📊 Dashboard Features

The Streamlit dashboard provides:

* Resume Upload
* Parsing Progress
* Resume Processed Count
* Profiles Created Count
* Weighted Parsing Accuracy
* Latest Extracted Candidate
* Candidate Table

---

# 📊 Weighted Parsing Accuracy

The parsing accuracy is calculated using weighted fields.

| Field          | Weight |
| -------------- | ------ |
| Name           | 20%    |
| Email          | 20%    |
| Skills         | 20%    |
| Education      | 15%    |
| Phone          | 10%    |
| Experience     | 10%    |
| Projects       | 3%     |
| Certifications | 2%     |

Total = **100%**

This provides a more realistic evaluation than simply counting filled fields.

---

# 📂 Database Schema

## Candidate Table

| Column         |
| -------------- |
| id             |
| name           |
| email          |
| phone          |
| education      |
| skills         |
| experience     |
| projects       |
| certifications |
| resume_path    |
| uploaded_at    |

---

## Upload History

Stores every uploaded resume to maintain the Resume Processed counter independently from candidate profiles.

---

# 🚀 Installation

## 1. Clone Repository

```bash
git clone https://github.com/yourusername/AI-Recruitment-Copilot.git

cd AI-Recruitment-Copilot
```

---

## 2. Create Virtual Environment

Windows

```bash
python -m venv venv
```

Activate

```bash
venv\Scripts\activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Download spaCy Model

```bash
python -m spacy download en_core_web_lg
```

---

## 5. Start FastAPI

```bash
uvicorn app.main:app --reload
```

Backend URL

```text
http://127.0.0.1:8000
```

---

## 6. Start Streamlit

Open another terminal

```bash
streamlit run streamlit_app.py
```

Frontend URL

```text
http://localhost:8501
```

---

# 📚 API Endpoints

## Upload Resume

```
POST /upload
```

Uploads and parses a resume.

---

## Get All Candidates

```
GET /candidates
```

Returns all stored candidates.

---

## Get Candidate

```
GET /candidate/{id}
```

Returns details of a specific candidate.

---

## Get Statistics

```
GET /stats
```

Returns:

* Resume Processed
* Profiles Created
* Parsing Accuracy

---

# 📦 Major Libraries Used

## FastAPI

Creates REST APIs for uploading resumes and retrieving candidate data.

---

## Streamlit

Builds the interactive frontend dashboard.

---

## spaCy

Processes resume text using NLP techniques.

---

## SQLAlchemy

Acts as an ORM to simplify database operations.

---

## SQLite

Stores candidate profiles locally.

---

## pypdf

Extracts text from PDF resumes.

---

## pdfplumber

Fallback parser for PDFs with complex layouts.

---

## python-docx

Reads Microsoft Word resumes.

---

## pandas

Displays candidate data in tabular form.

---

## requests

Allows Streamlit to communicate with the FastAPI backend.

---

## JSON

Converts Python lists into strings before storing them in SQLite and converts them back while displaying.

---

# 💡 Current Features

* PDF Resume Parsing
* DOCX Resume Parsing
* NLP-based Extraction
* Skills Detection
* Education Detection
* Experience Detection
* Project Detection
* Certification Detection
* SQLite Storage
* Candidate Dashboard
* Upload History
* Weighted Parsing Accuracy
* Responsive UI

---

# 🔮 Future Enhancements

* OCR support for scanned resumes
* AI-powered Resume Ranking
* Job Description Matching
* Resume Similarity Score
* Duplicate Resume Detection
* Export to Excel/PDF
* Recruiter Authentication
* Email Notifications
* PostgreSQL/MySQL Support
* Cloud Deployment

---

# 📸 Screenshots

> Add screenshots of:

* Dashboard
* Resume Upload
* Candidate Profile
* Candidate Table
* Parsing Progress
* Analytics Cards

---

# 👨‍💻 Developed By

**Pravesh Nirmal**

B.Tech Computer Science & Engineering

AI | Backend Development | FastAPI | Python | NLP

---

# 📜 License

This project is developed for educational and learning purposes. Feel free to modify and extend it for personal or academic use.

---

# ⭐ If you like this project

If this project helped you, consider giving it a ⭐ on GitHub to support its development!
