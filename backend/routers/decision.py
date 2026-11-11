from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Applicant, LoanApplication, CIBILRecord
from backend.schemas import DecisionEvaluationRequest, DecisionEvaluationResponse
from backend.services.blockchain_service import BlockchainService
from backend.services.ml_service import MLService
from backend.services.monitoring_service import monitoring_service
from backend.routers.applicant import calculate_emi

router = APIRouter(prefix="/api/decision", tags=["Composite Decision Engine"])

@router.post("/evaluate", response_model=DecisionEvaluationResponse)
def evaluate_loan_decision(req: DecisionEvaluationRequest, db: Session = Depends(get_db)):
    loan = db.query(LoanApplication).filter(LoanApplication.application_id == req.application_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan application not found")

    applicant = db.query(Applicant).filter(Applicant.applicant_id == loan.applicant_id).first()
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")

    # 1. Evaluate Identity Gate
    identity_pass = (loan.identity_status == "VERIFIED")
    
    # 2. Evaluate Face Biometric Gate
    face_pass = (loan.face_status == "VERIFIED")
    
    # 3. Evaluate OTP Gate
    otp_pass = (loan.otp_status == "VERIFIED")
    
    # 4. Evaluate CIBIL Gate
    cibil_pass = (loan.cibil_status == "VERIFIED")
    cibil_mismatch = (loan.cibil_status == "MISMATCH")
    
    # 5. Evaluate Blockchain Integrity Gate
    is_chain_valid, tampered_indices, _ = BlockchainService.verify_chain_integrity(db)
    blockchain_pass = is_chain_valid
    loan.blockchain_status = "VALID" if is_chain_valid else "TAMPER_DETECTED"
    
    # 6. Evaluate ML Risk Gate
    if not loan.risk_category:
        cibil_score = loan.cibil_score or 720
        monthly_emi = loan.monthly_emi or calculate_emi(loan.loan_amount, 10.5, loan.loan_tenure_months)
        total_monthly_obligations = (applicant.existing_emi or 0.0) + monthly_emi
        dti_ratio = round(total_monthly_obligations / (applicant.monthly_income + 1e-6), 4)
        
        ml_res = MLService.predict_credit_risk({
            "monthly_income": applicant.monthly_income,
            "loan_amount": loan.loan_amount,
            "loan_tenure_months": loan.loan_tenure_months,
            "cibil_score": cibil_score,
            "active_loans_count": 1,
            "total_overdue_amount": 0.0,
            "credit_utilization_ratio": 0.25,
            "dti_ratio": dti_ratio
        })
        loan.dti_ratio = dti_ratio
        loan.risk_category = ml_res["risk_category"]
        loan.risk_probability = ml_res["risk_probability"]

    risk_pass = (loan.risk_category in ["LOW", "MEDIUM"]) and (loan.risk_probability < 0.65)
    dti_pass = (loan.dti_ratio or 0.3) <= 0.55

    gates = {
        "identity_verification": {"status": loan.identity_status, "passed": identity_pass},
        "face_biometrics": {"status": loan.face_status, "passed": face_pass},
        "otp_authentication": {"status": loan.otp_status, "passed": otp_pass},
        "cibil_verification": {"status": loan.cibil_status, "passed": cibil_pass},
        "blockchain_integrity": {"status": loan.blockchain_status, "passed": blockchain_pass},
        "ml_credit_risk": {"status": loan.risk_category, "probability": loan.risk_probability, "passed": risk_pass},
        "dti_solvency": {"dti_ratio": loan.dti_ratio, "passed": dti_pass}
    }

    # Composite Rule Evaluation
    if cibil_mismatch or not blockchain_pass:
        final_decision = "MANUAL_REVIEW"
        approved_amount = 0.0
        reason = "Flagged for Underwriter Review: Identity correlation mismatch or blockchain ledger anomaly detected."
    elif not identity_pass or not face_pass or not otp_pass:
        final_decision = "MANUAL_REVIEW"
        approved_amount = 0.0
        reason = "Identity authentication incomplete or flagged. Requires manual KYC officer review."
    elif loan.risk_category == "HIGH" or not dti_pass:
        final_decision = "REJECTED"
        approved_amount = 0.0
        reason = f"Credit policy criteria not met: High Default Risk ({loan.risk_probability*100:.1f}%) or High DTI ({loan.dti_ratio*100:.1f}%)."
    elif identity_pass and face_pass and otp_pass and cibil_pass and blockchain_pass and risk_pass:
        final_decision = "APPROVED"
        approved_amount = loan.loan_amount
        reason = f"All 7 Verification & Risk gates successfully passed. Auto-approved for INR {loan.loan_amount:,.0f}."
        
        # Write to Blockchain Integrity Layer
        verif_payload = {
            "application_id": loan.application_id,
            "applicant_id": applicant.applicant_id,
            "identity_status": loan.identity_status,
            "face_status": loan.face_status,
            "otp_status": loan.otp_status,
            "cibil_score": loan.cibil_score or 750,
            "risk_category": loan.risk_category,
            "decision": "APPROVED"
        }
        BlockchainService.create_verification_block(
            db=db,
            applicant_id=applicant.applicant_id,
            cibil_control_number=f"CIBIL-REC-{loan.applicant_id}",
            credit_score=loan.cibil_score or 750,
            verification_payload=verif_payload
        )
    else:
        final_decision = "MANUAL_REVIEW"
        approved_amount = 0.0
        reason = "Underwriter manual review required."

    loan.final_decision = final_decision
    loan.approved_amount = approved_amount
    loan.decision_reason = reason
    db.commit()

    monitoring_service.record_event(
        stage="DECISION_AI",
        event_type="SANCTION_EVALUATED",
        status="SUCCESS" if final_decision == "APPROVED" else ("REVIEW" if final_decision == "MANUAL_REVIEW" else "REJECTED"),
        details=f"Decision: {final_decision} ({reason})",
        applicant_id=applicant.applicant_id,
        duration_ms=130,
        is_anomaly=(final_decision == "REJECTED")
    )

    return DecisionEvaluationResponse(
        application_id=loan.application_id,
        final_decision=final_decision,
        approved_amount=approved_amount,
        interest_rate=loan.interest_rate,
        monthly_emi=loan.monthly_emi,
        decision_reason=reason,
        rule_breakdown=gates
    )
