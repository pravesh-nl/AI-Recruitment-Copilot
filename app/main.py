from fastapi import FastAPI
from app.database import Base, engine
from app.models.upload_history import UploadHistory
from app.models.candidate import Candidate
from app.routes.upload import router as upload_router
from app.routes.candidate import router as candidate_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Recruitm-ent Copilot",
    version="1.0.0"
)

app.include_router(upload_router)
app.include_router(candidate_router)

@app.get("/")
def root():
    return {
        "message": "AI Recruitment Copilot API is running!"
    }