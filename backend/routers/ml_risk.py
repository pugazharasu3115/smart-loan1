import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Applicant, LoanApplication, CIBILRecord
from backend.schemas import MLRiskPredictionRequest, MLRiskPredictionResponse
from backend.services.ml_service import MLService
from backend.routers.applicant import calculate_emi

router = APIRouter(prefix="/api/ml", tags=["ML Credit Risk & SHAP Explainability"])

@router.post("/predict")
def predict_credit_risk(req: MLRiskPredictionRequest):
    # Calculate loan monthly EMI
    monthly_emi = calculate_emi(req.loan_amount, 10.5, req.loan_tenure_months)
    total_monthly_obligations = req.existing_emi + monthly_emi
    dti_ratio = round(total_monthly_obligations / (req.monthly_income + 1e-6), 4)

    payload = {
        "monthly_income": req.monthly_income,
        "loan_amount": req.loan_amount,
        "loan_tenure_months": req.loan_tenure_months,
        "cibil_score": req.cibil_score,
        "active_loans_count": req.active_loans_count,
        "total_overdue_amount": req.total_overdue_amount,
        "credit_utilization_ratio": req.credit_utilization_ratio,
        "dti_ratio": dti_ratio
    }

    result = MLService.predict_credit_risk(payload)
    return result

@router.post("/predict-for-application/{application_id}")
def predict_for_application(application_id: str, db: Session = Depends(get_db)):
    loan = db.query(LoanApplication).filter(LoanApplication.application_id == application_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan application not found")

    applicant = db.query(Applicant).filter(Applicant.applicant_id == loan.applicant_id).first()
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant profile not found")

    # Get CIBIL data or defaults
    cibil_score = loan.cibil_score or 720
    active_loans = 1
    overdue_amt = 0.0
    utilization = 0.25

    # Check if applicant matches seeded CIBIL record
    cibil_rec = db.query(CIBILRecord).filter(CIBILRecord.pan_number == applicant.pan_number).first()
    if cibil_rec:
        cibil_score = cibil_rec.credit_score
        active_loans = cibil_rec.active_loans_count
        overdue_amt = cibil_rec.total_overdue_amount
        utilization = cibil_rec.credit_utilization_ratio

    total_monthly_obligations = (applicant.existing_emi or 0.0) + (loan.monthly_emi or 0.0)
    dti_ratio = round(total_monthly_obligations / (applicant.monthly_income + 1e-6), 4)

    payload = {
        "monthly_income": applicant.monthly_income,
        "loan_amount": loan.loan_amount,
        "loan_tenure_months": loan.loan_tenure_months,
        "cibil_score": cibil_score,
        "active_loans_count": active_loans,
        "total_overdue_amount": overdue_amt,
        "credit_utilization_ratio": utilization,
        "dti_ratio": dti_ratio
    }

    ml_res = MLService.predict_credit_risk(payload)

    # Save to loan application
    loan.cibil_score = cibil_score
    loan.dti_ratio = dti_ratio
    loan.risk_category = ml_res["risk_category"]
    loan.risk_probability = ml_res["risk_probability"]
    loan.shap_explanation_json = json.dumps(ml_res["shap_contributions"])
    db.commit()

    return {
        "application_id": loan.application_id,
        "applicant_id": loan.applicant_id,
        **ml_res
    }

@router.get("/model-metrics")
def get_model_metrics():
    model_data = MLService.load_model()
    return {
        "model_comparison": model_data.get("comparison_results", {}),
        "feature_importances": model_data.get("feature_importances", {}),
        "selected_best_model": "Gradient Boosting Classifier",
        "evaluation_criteria": ["Accuracy", "Precision", "Recall", "F1_Score", "ROC_AUC"]
    }
