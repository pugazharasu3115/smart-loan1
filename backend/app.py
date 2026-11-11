import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.database import engine, Base
from backend.seed_data import seed_database
from backend.routers import (
    auth,
    applicant,
    ocr,
    face,
    otp,
    cibil,
    blockchain,
    ml_risk,
    decision,
    admin,
    monitoring
)

# Initialize database schema and pre-populate seed data
Base.metadata.create_all(bind=engine)
try:
    seed_database()
except Exception as e:
    print(f"Seed info: {e}")

app = FastAPI(
    title="Smart Loan Verification & Approval System",
    description="Academic Prototype: Blockchain-Based Loan System with OCR, Face Biometrics, CIBIL Verification, and Explainable AI (SHAP)",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router)
app.include_router(applicant.router)
app.include_router(ocr.router)
app.include_router(face.router)
app.include_router(otp.router)
app.include_router(cibil.router)
app.include_router(blockchain.router)
app.include_router(ml_risk.router)
app.include_router(decision.router)
app.include_router(admin.router)
app.include_router(monitoring.router)

# Mount Frontend static files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
def serve_index():
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Smart Loan System API is live. Visit /docs for Swagger documentation."}

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "system": "Smart Loan Verification and Approval System",
        "blockchain_layer": "Active (SHA-256)",
        "ml_engine": "Gradient Boosting + SHAP (Active)"
    }
