from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from backend.database import get_db
from backend.models import LoanApplication, Applicant, BlockchainBlock, DocumentRecord, CIBILRecord
from backend.security import decrypt_field

router = APIRouter(prefix="/api/admin", tags=["Admin Dashboard & Underwriter Management"])

class AdminActionRequest(BaseModel):
    action: str # "APPROVE", "REJECT", "REQUEST_INFO"
    admin_notes: Optional[str] = None
    approved_amount: Optional[float] = None

@router.get("/metrics")
def get_admin_metrics(db: Session = Depends(get_db)):
    """Computes high-level aggregated statistics for the bank officer dashboard."""
    total_apps = db.query(LoanApplication).count()
    approved_apps = db.query(LoanApplication).filter(LoanApplication.final_decision == "APPROVED").count()
    rejected_apps = db.query(LoanApplication).filter(LoanApplication.final_decision == "REJECTED").count()
    review_apps = db.query(LoanApplication).filter(LoanApplication.final_decision == "MANUAL_REVIEW").count()
    pending_apps = db.query(LoanApplication).filter(LoanApplication.final_decision == "PENDING").count()

    total_disbursed = db.query(func.sum(LoanApplication.approved_amount)).scalar() or 0.0
    avg_loan_ticket = db.query(func.avg(LoanApplication.loan_amount)).scalar() or 0.0
    avg_cibil = db.query(func.avg(LoanApplication.cibil_score)).filter(LoanApplication.cibil_score.isnot(None)).scalar() or 742.0

    # Risk Distribution
    low_risk = db.query(LoanApplication).filter(LoanApplication.risk_category == "LOW").count()
    med_risk = db.query(LoanApplication).filter(LoanApplication.risk_category == "MEDIUM").count()
    high_risk = db.query(LoanApplication).filter(LoanApplication.risk_category == "HIGH").count()

    total_blocks = db.query(BlockchainBlock).count()

    return {
        "summary": {
            "total_applications": total_apps,
            "approved": approved_apps,
            "rejected": rejected_apps,
            "manual_review_queue": review_apps,
            "pending": pending_apps,
            "approval_rate": round((approved_apps / total_apps * 100) if total_apps > 0 else 0.0, 1),
            "total_sanctioned_amount": round(float(total_disbursed), 2),
            "avg_loan_amount": round(float(avg_loan_ticket), 2),
            "avg_cibil_score": round(float(avg_cibil), 0)
        },
        "risk_distribution": {
            "low_risk": low_risk,
            "medium_risk": med_risk,
            "high_risk": high_risk
        },
        "blockchain_ledger": {
            "total_blocks_chained": total_blocks,
            "integrity_status": "SECURED"
        }
    }

@router.get("/applications")
def list_all_applications(
    status_filter: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Lists all loan applications with applicant details and verification statuses."""
    query = db.query(LoanApplication, Applicant).join(
        Applicant, LoanApplication.applicant_id == Applicant.applicant_id
    )

    if status_filter and status_filter.upper() != "ALL":
        query = query.filter(LoanApplication.final_decision == status_filter.upper())

    results = query.order_by(LoanApplication.id.desc()).all()
    
    app_list = []
    for loan, applicant in results:
        # Search match if provided
        if search:
            s = search.lower()
            if s not in loan.application_id.lower() and s not in applicant.full_name.lower() and s not in applicant.applicant_id.lower():
                continue

        app_list.append({
            "application_id": loan.application_id,
            "applicant_id": loan.applicant_id,
            "applicant_name": applicant.full_name,
            "mobile": applicant.mobile,
            "loan_amount": loan.loan_amount,
            "tenure_months": loan.loan_tenure_months,
            "loan_purpose": loan.loan_purpose,
            "monthly_income": applicant.monthly_income,
            "identity_status": loan.identity_status,
            "face_status": loan.face_status,
            "otp_status": loan.otp_status,
            "cibil_status": loan.cibil_status,
            "cibil_score": loan.cibil_score,
            "blockchain_status": loan.blockchain_status,
            "risk_category": loan.risk_category or "PENDING",
            "risk_probability": loan.risk_probability,
            "final_decision": loan.final_decision,
            "approved_amount": loan.approved_amount,
            "decision_reason": loan.decision_reason,
            "created_at": loan.created_at.strftime("%Y-%m-%d %H:%M") if loan.created_at else ""
        })

    return app_list

@router.get("/application/{application_id}/audit-trail")
def get_application_audit_trail(application_id: str, db: Session = Depends(get_db)):
    """Provides detailed step-by-step verification history and documents for deep underwriter drilldown."""
    loan = db.query(LoanApplication).filter(LoanApplication.application_id == application_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Application not found")

    applicant = db.query(Applicant).filter(Applicant.applicant_id == loan.applicant_id).first()
    docs = db.query(DocumentRecord).filter(DocumentRecord.applicant_id == loan.applicant_id).all()
    block = db.query(BlockchainBlock).filter(BlockchainBlock.applicant_id == loan.applicant_id).first()

    return {
        "application": {
            "application_id": loan.application_id,
            "loan_amount": loan.loan_amount,
            "tenure_months": loan.loan_tenure_months,
            "purpose": loan.loan_purpose,
            "final_decision": loan.final_decision,
            "decision_reason": loan.decision_reason,
            "approved_amount": loan.approved_amount,
            "admin_notes": loan.admin_notes
        },
        "applicant": {
            "applicant_id": applicant.applicant_id,
            "full_name": applicant.full_name,
            "dob": applicant.dob,
            "mobile": applicant.mobile,
            "email": applicant.email,
            "address": applicant.address,
            "pan_number": decrypt_field(applicant.pan_number),
            "monthly_income": applicant.monthly_income,
            "existing_emi": applicant.existing_emi
        },
        "verification_stages": {
            "identity_ocr": {
                "status": loan.identity_status,
                "documents_count": len(docs),
                "docs": [{"type": d.doc_type, "match_score": d.match_score, "is_verified": d.is_verified, "hash": d.file_hash} for d in docs]
            },
            "face_biometrics": {
                "status": loan.face_status
            },
            "otp_authentication": {
                "status": loan.otp_status
            },
            "cibil_verification": {
                "status": loan.cibil_status,
                "credit_score": loan.cibil_score
            },
            "blockchain_record": {
                "status": loan.blockchain_status,
                "block_index": block.block_index if block else None,
                "block_hash": block.block_hash if block else None,
                "previous_hash": block.previous_hash if block else None
            },
            "ml_risk_model": {
                "risk_category": loan.risk_category,
                "risk_probability": loan.risk_probability,
                "dti_ratio": loan.dti_ratio,
                "shap_explanation": loan.shap_explanation_json
            }
        }
    }

@router.post("/application/{application_id}/action")
def update_application_decision(application_id: str, req: AdminActionRequest, db: Session = Depends(get_db)):
    """Allows bank underwriter to manually approve or reject flagged applications."""
    loan = db.query(LoanApplication).filter(LoanApplication.application_id == application_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Application not found")

    loan.final_decision = req.action
    loan.admin_notes = req.admin_notes or f"Manual underwriter decision: {req.action}"
    if req.action == "APPROVED":
        loan.approved_amount = req.approved_amount if req.approved_amount else loan.loan_amount
        loan.decision_reason = f"Manual Underwriter Approval. Notes: {loan.admin_notes}"
    elif req.action == "REJECTED":
        loan.approved_amount = 0.0
        loan.decision_reason = f"Manual Underwriter Rejection. Reason: {loan.admin_notes}"

    db.commit()
    db.refresh(loan)

    return {
        "success": True,
        "application_id": loan.application_id,
        "status": loan.final_decision,
        "approved_amount": loan.approved_amount,
        "notes": loan.admin_notes
    }
