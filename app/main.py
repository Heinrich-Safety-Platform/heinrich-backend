from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(
    title="Heinrich Safety Layer Engine",
    description="하인리히 법칙 기반 공간 위험도 분석 API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static/images", StaticFiles(directory=UPLOAD_DIR), name="images")

@app.get("/health")
def health_check():
    return {"status": "healthy", "engine": "Heinrich Safety API v1"}