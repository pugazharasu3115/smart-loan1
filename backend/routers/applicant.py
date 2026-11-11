import random
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Applicant, LoanApplication, User
from backend.schemas import ApplicantCreateRequest, LoanApplicationCreateRequest
from backend.security import encrypt_field, decrypt_field, get_current_user

router = APIRouter(prefix="/api/applicant", tags=["Applicant Management"])

def generate_applicant_id() -> str:
    year = datetime.utcnow().year
    rand_num = random.randint(100000, 999999)
    return f"APP-{year}-{rand_num}"

def generate_loan_id() -> str:
    year = datetime.utcnow().year
    rand_num = random.randint(100000, 999999)
    return f"LN-{year}-{rand_num}"

def calculate_emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    if principal <= 0 or tenure_months <= 0:
        return 0.0
    r = (annual_rate / 100.0) / 12.0
    if r == 0:
        return round(principal / tenure_months, 2)
    emi = principal * r * ((1 + r) ** tenure_months) / (((1 + r) ** tenure_months) - 1)
    return round(float(emi), 2)

@router.post("/profile")
def create_or_update_applicant(req: ApplicantCreateRequest, db: Session = Depends(get_db)):
    # Check if applicant already registered with this mobile or email
    existing = db.query(Applicant).filter(
        (Applicant.mobile == req.mobile) | (Applicant.email == req.email)
    ).first()

    if existing:
        # Update existing profile
        existing.full_name = req.full_name
        existing.dob = req.dob
        existing.address = req.address or existing.address
        existing.pan_number = encrypt_field(req.pan_number)
        if req.aadhaar_number:
            existing.aadhaar_number = encrypt_field(req.aadhaar_number)
        existing.employment_type = req.employment_type
        existing.monthly_income = req.monthly_income
        existing.existing_emi = req.existing_emi or 0.0
        db.commit()
        db.refresh(existing)
        applicant = existing
    else:
        new_app_id = generate_applicant_id()
        applicant = Applicant(
            applicant_id=new_app_id,
            full_name=req.full_name,
            dob=req.dob,
            mobile=req.mobile,
            email=req.email,
            address=req.address,
            pan_number=encrypt_field(req.pan_number),
            aadhaar_number=encrypt_field(req.aadhaar_number) if req.aadhaar_number else None,
            employment_type=req.employment_type,
            monthly_income=req.monthly_income,
            existing_emi=req.existing_emi or 0.0
        )
        db.add(applicant)
        db.commit()
        db.refresh(applicant)

    return {
        "success": True,
        "message": "Applicant profile saved successfully",
        "applicant_id": applicant.applicant_id,
        "full_name": applicant.full_name,
        "dob": applicant.dob,
        "mobile": applicant.mobile,
        "email": applicant.email,
        "pan_number": decrypt_field(applicant.pan_number),
        "employment_type": applicant.employment_type,
        "monthly_income": applicant.monthly_income
    }

@router.get("/{applicant_id}")
def get_applicant(applicant_id: str, db: Session = Depends(get_db)):
    applicant = db.query(Applicant).filter(Applicant.applicant_id == applicant_id).first()
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")
    
    return {
        "applicant_id": applicant.applicant_id,
        "full_name": applicant.full_name,
        "dob": applicant.dob,
        "mobile": applicant.mobile,
        "email": applicant.email,
        "address": applicant.address,
        "pan_number": decrypt_field(applicant.pan_number),
        "aadhaar_number": decrypt_field(applicant.aadhaar_number) if applicant.aadhaar_number else None,
        "employment_type": applicant.employment_type,
        "monthly_income": applicant.monthly_income,
        "existing_emi": applicant.existing_emi,
        "created_at": applicant.created_at
    }

@router.post("/loan-apply")
def submit_loan_application(req: LoanApplicationCreateRequest, db: Session = Depends(get_db)):
    applicant = db.query(Applicant).filter(Applicant.applicant_id == req.applicant_id).first()
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant profile must be created first")

    # Standard starting interest rate
    interest_rate = 10.5
    monthly_emi = calculate_emi(req.loan_amount, interest_rate, req.loan_tenure_months)
    loan_id = generate_loan_id()

    loan = LoanApplication(
        application_id=loan_id,
        applicant_id=req.applicant_id,
        loan_amount=req.loan_amount,
        loan_tenure_months=req.loan_tenure_months,
        loan_purpose=req.loan_purpose,
        interest_rate=interest_rate,
        monthly_emi=monthly_emi,
        identity_status="PENDING",
        face_status="PENDING",
        otp_status="PENDING",
        cibil_status="PENDING",
        blockchain_status="PENDING",
        final_decision="PENDING"
    )
    db.add(loan)
    db.commit()
    db.refresh(loan)

    return {
        "success": True,
        "application_id": loan.application_id,
        "applicant_id": loan.applicant_id,
        "loan_amount": loan.loan_amount,
        "loan_tenure_months": loan.loan_tenure_months,
        "monthly_emi": loan.monthly_emi,
        "interest_rate": loan.interest_rate,
        "status": loan.final_decision
    }

@router.get("/loan/{application_id}")
def get_loan_details(application_id: str, db: Session = Depends(get_db)):
    loan = db.query(LoanApplication).filter(LoanApplication.application_id == application_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan application not found")
    
    applicant = db.query(Applicant).filter(Applicant.applicant_id == loan.applicant_id).first()
    
    return {
        "application_id": loan.application_id,
        "applicant_id": loan.applicant_id,
        "applicant_name": applicant.full_name if applicant else "N/A",
        "loan_amount": loan.loan_amount,
        "loan_tenure_months": loan.loan_tenure_months,
        "loan_purpose": loan.loan_purpose,
        "interest_rate": loan.interest_rate,
        "monthly_emi": loan.monthly_emi,
        "identity_status": loan.identity_status,
        "face_status": loan.face_status,
        "otp_status": loan.otp_status,
        "cibil_status": loan.cibil_status,
        "blockchain_status": loan.blockchain_status,
        "cibil_score": loan.cibil_score,
        "dti_ratio": loan.dti_ratio,
        "risk_category": loan.risk_category,
        "risk_probability": loan.risk_probability,
        "shap_explanation_json": loan.shap_explanation_json,
        "final_decision": loan.final_decision,
        "decision_reason": loan.decision_reason,
        "approved_amount": loan.approved_amount,
        "admin_notes": loan.admin_notes,
        "created_at": loan.created_at
    }
