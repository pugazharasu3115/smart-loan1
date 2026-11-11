from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Applicant, CIBILRecord, LoanApplication
from backend.schemas import CIBILVerifyRequest, CIBILVerifyResponse
from backend.services.ocr_service import string_similarity
from backend.security import decrypt_field
from backend.services.monitoring_service import monitoring_service

router = APIRouter(prefix="/api/cibil", tags=["Mock CIBIL Credit Bureau Verification"])

@router.get("/records")
def list_cibil_records(db: Session = Depends(get_db)):
    """Returns all seeded mock CIBIL records for inspection and demo setup."""
    records = db.query(CIBILRecord).all()
    return records

@router.post("/verify", response_model=CIBILVerifyResponse)
def verify_cibil_identity(req: CIBILVerifyRequest, db: Session = Depends(get_db)):
    applicant = db.query(Applicant).filter(Applicant.applicant_id == req.applicant_id).first()
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")

    # 1. Search for records by PAN first
    pan_cleaned = req.pan_number.strip().upper()
    cibil_by_pan = db.query(CIBILRecord).filter(CIBILRecord.pan_number == pan_cleaned).first()
    
    # 2. Also search for any record matching Name to test multi-attribute mismatch
    cibil_all = db.query(CIBILRecord).all()
    name_matched_record = None
    for r in cibil_all:
        if string_similarity(r.full_name, req.full_name) >= 0.85:
            name_matched_record = r
            break

    target_record = cibil_by_pan or name_matched_record

    if not target_record:
        # No bureau record found at all
        loan = db.query(LoanApplication).filter(LoanApplication.applicant_id == req.applicant_id).order_by(LoanApplication.id.desc()).first()
        if loan:
            loan.cibil_status = "NOT_FOUND"
            db.commit()
            
        return CIBILVerifyResponse(
            applicant_id=req.applicant_id,
            is_verified=False,
            status="NOT_FOUND",
            comparison_matrix={"name": False, "dob": False, "pan": False, "mobile": False},
            mismatch_details="No credit bureau history found matching the provided identity."
        )

    # Multi-attribute comparison matrix
    name_sim = string_similarity(target_record.full_name, req.full_name)
    name_ok = name_sim >= 0.80
    dob_ok = (target_record.dob.replace("/", "-") == req.dob.replace("/", "-"))
    pan_ok = (target_record.pan_number.upper() == pan_cleaned)
    mobile_ok = (target_record.mobile_number[-10:] == req.mobile[-10:])

    matrix = {
        "name": name_ok,
        "dob": dob_ok,
        "pan": pan_ok,
        "mobile": mobile_ok
    }

    # KEY ACADEMIC SCENARIO: Same name but different PAN / DOB / Mobile (Impersonation catch)
    if name_ok and (not pan_ok or not dob_ok or not mobile_ok):
        status_result = "MISMATCH"
        is_verified = False
        mismatch_msg = (
            f"MULTI-ATTRIBUTE MISMATCH DETECTED: Name '{req.full_name}' matched bureau profile, "
            f"but PAN ({pan_cleaned} vs {target_record.pan_number}), "
            f"DOB ({req.dob} vs {target_record.dob}), or "
            f"Mobile ({req.mobile} vs {target_record.mobile_number}) failed correlation check. "
            f"FLAGGED AS POTENTIAL IMPERSONATION -> HOLD FOR MANUAL REVIEW."
        )
    elif name_ok and pan_ok and (dob_ok or mobile_ok):
        status_result = "VERIFIED"
        is_verified = True
        mismatch_msg = None
    else:
        status_result = "MISMATCH"
        is_verified = False
        mismatch_msg = "Multi-attribute verification failed across identity parameters."

    # Update loan application
    loan = db.query(LoanApplication).filter(LoanApplication.applicant_id == req.applicant_id).order_by(LoanApplication.id.desc()).first()
    if loan:
        loan.cibil_status = status_result
        if is_verified:
            loan.cibil_score = target_record.credit_score
        db.commit()

    monitoring_service.record_event(
        stage="CIBIL",
        event_type="BUREAU_PULL",
        status="SUCCESS" if is_verified else "MISMATCH",
        details=f"Score: {target_record.credit_score if is_verified else 'N/A'}. Result: {status_result}.",
        applicant_id=req.applicant_id,
        duration_ms=180,
        is_anomaly=(not is_verified or (target_record.credit_score and target_record.credit_score < 600))
    )

    return CIBILVerifyResponse(
        applicant_id=req.applicant_id,
        cibil_control_number=target_record.cibil_control_number,
        credit_score=target_record.credit_score if is_verified else None,
        is_verified=is_verified,
        status=status_result,
        comparison_matrix=matrix,
        mismatch_details=mismatch_msg,
        active_loans_count=target_record.active_loans_count if is_verified else 0,
        total_active_loan_amount=target_record.total_active_loan_amount if is_verified else 0.0,
        total_overdue_amount=target_record.total_overdue_amount if is_verified else 0.0,
        credit_utilization_ratio=target_record.credit_utilization_ratio if is_verified else 0.0,
        payment_history_score=target_record.payment_history_score if is_verified else 0.0
    )
