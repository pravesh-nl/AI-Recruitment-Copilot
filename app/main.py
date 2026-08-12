from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.models.upload_history import UploadHistory
from app.models.candidate import Candidate
from app.models.job import Job
from app.routes.job import router as job_router
from app.routes.upload import router as upload_router
from app.routes.candidate import router as candidate_router
from app.routes.matching import router as matching_router
from app.routes.interview import router as interview_router
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Recruitment Copilot",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(candidate_router)
app.include_router(job_router)
app.include_router(matching_router)
app.include_router(interview_router)

@app.get("/")
def root():
    return {
        "message": "AI Recruitment Copilot API is running!"
    }
    