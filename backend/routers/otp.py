import pyotp
import random
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Applicant, OTPVerification, LoanApplication
from backend.schemas import OTPGenerateRequest, OTPVerifyRequest, OTPResponse

router = APIRouter(prefix="/api/otp", tags=["OTP Verification Module"])

@router.post("/generate", response_model=OTPResponse)
def generate_otp(req: OTPGenerateRequest, db: Session = Depends(get_db)):
    applicant = db.query(Applicant).filter(Applicant.applicant_id == req.applicant_id).first()
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")

    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret, interval=300) # 5-minute validity
    otp_code = totp.now()

    expires_at = datetime.utcnow() + timedelta(minutes=5)
    
    otp_record = OTPVerification(
        applicant_id=applicant.applicant_id,
        mobile_number=req.mobile or applicant.mobile,
        secret_key=secret,
        generated_otp=otp_code,
        is_verified=False,
        attempts=0,
        expires_at=expires_at
    )
    db.add(otp_record)
    db.commit()

    simulated_sms_text = f"[SmartLoan Auth] Your OTP code is {otp_code}. Valid for 5 mins. Do not share with anyone."
    print(f"\n--- [SIMULATED SMS GATEWAY] To: {applicant.mobile} ---\n{simulated_sms_text}\n------------------------------------------\n")

    return OTPResponse(
        applicant_id=applicant.applicant_id,
        is_verified=False,
        message=f"OTP successfully dispatched to registered mobile +91-{applicant.mobile[-4:]}",
        simulated_otp=otp_code
    )

@router.post("/verify", response_model=OTPResponse)
def verify_otp(req: OTPVerifyRequest, db: Session = Depends(get_db)):
    record = db.query(OTPVerification).filter(
        OTPVerification.applicant_id == req.applicant_id
    ).order_by(OTPVerification.id.desc()).first()

    if not record:
        raise HTTPException(status_code=400, detail="No active OTP found. Please request a new OTP.")

    if datetime.utcnow() > record.expires_at:
        raise HTTPException(status_code=400, detail="OTP has expired. Please generate a new one.")

    if record.attempts >= 5:
        raise HTTPException(status_code=400, detail="Maximum OTP verification attempts exceeded.")

    record.attempts += 1

    if req.otp_entered.strip() == record.generated_otp.strip():
        record.is_verified = True
        db.commit()

        loan = db.query(LoanApplication).filter(
            LoanApplication.applicant_id == req.applicant_id
        ).order_by(LoanApplication.id.desc()).first()
        if loan:
            loan.otp_status = "VERIFIED"
            db.commit()

        return OTPResponse(
            applicant_id=req.applicant_id,
            is_verified=True,
            message="Mobile possession successfully verified via TOTP.",
            simulated_otp=None
        )
    else:
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid OTP entered. Please try again.")
