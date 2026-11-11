from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# --- Auth Schemas ---
class UserRegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    role: Optional[str] = "applicant"

class UserLoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
    applicant_id: Optional[str] = None

# --- Applicant & Loan Schemas ---
class ApplicantCreateRequest(BaseModel):
    full_name: str
    dob: str # YYYY-MM-DD
    mobile: str
    email: str
    address: Optional[str] = None
    pan_number: str
    aadhaar_number: Optional[str] = None
    employment_type: str = "Salaried"
    monthly_income: float
    existing_emi: Optional[float] = 0.0

class LoanApplicationCreateRequest(BaseModel):
    applicant_id: str
    loan_amount: float
    loan_tenure_months: int
    loan_purpose: str = "Personal"

class LoanApplicationResponse(BaseModel):
    id: int
    application_id: str
    applicant_id: str
    loan_amount: float
    loan_tenure_months: int
    loan_purpose: str
    interest_rate: float
    monthly_emi: float
    identity_status: str
    face_status: str
    otp_status: str
    cibil_status: str
    blockchain_status: str
    cibil_score: Optional[int] = None
    dti_ratio: Optional[float] = None
    risk_category: Optional[str] = None
    risk_probability: Optional[float] = None
    shap_explanation_json: Optional[str] = None
    final_decision: str
    decision_reason: Optional[str] = None
    approved_amount: float
    admin_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

# --- OCR & Document Schemas ---
class DocumentOCRResponse(BaseModel):
    doc_type: str
    file_name: str
    file_hash: str
    extracted_data: Dict[str, Any]
    match_score: float
    is_verified: bool
    mismatch_reasons: List[str]

# --- Face Verification Schemas ---
class FaceVerificationRequest(BaseModel):
    applicant_id: str
    image_base64: str # Captured from webcam
    reference_image_base64: Optional[str] = None # Optional custom reference or from ID

class FaceVerificationResponse(BaseModel):
    applicant_id: str
    similarity_score: float
    threshold: float
    is_matched: bool
    live_face_hash: str
    status: str
    message: str

# --- OTP Schemas ---
class OTPGenerateRequest(BaseModel):
    applicant_id: str
    mobile: str

class OTPVerifyRequest(BaseModel):
    applicant_id: str
    otp_entered: str

class OTPResponse(BaseModel):
    applicant_id: str
    is_verified: bool
    message: str
    simulated_otp: Optional[str] = None

# --- CIBIL Schemas ---
class CIBILVerifyRequest(BaseModel):
    applicant_id: str
    full_name: str
    dob: str
    pan_number: str
    mobile: str

class CIBILVerifyResponse(BaseModel):
    applicant_id: str
    cibil_control_number: Optional[str] = None
    credit_score: Optional[int] = None
    is_verified: bool
    status: str # VERIFIED / MISMATCH / NOT_FOUND
    comparison_matrix: Dict[str, bool]
    mismatch_details: Optional[str] = None
    active_loans_count: Optional[int] = 0
    total_active_loan_amount: Optional[float] = 0.0
    total_overdue_amount: Optional[float] = 0.0
    credit_utilization_ratio: Optional[float] = 0.0
    payment_history_score: Optional[float] = 0.0

# --- Blockchain Schemas ---
class BlockchainRecordResponse(BaseModel):
    block_index: int
    previous_hash: str
    block_hash: str
    applicant_id: str
    cibil_control_number: str
    credit_score_hash: str
    verification_data_hash: str
    timestamp: datetime
    is_valid: bool

class BlockchainAuditResponse(BaseModel):
    total_blocks: int
    is_chain_valid: bool
    tampered_block_indices: List[int]
    audit_report: str

# --- ML & SHAP Schemas ---
class MLRiskPredictionRequest(BaseModel):
    monthly_income: float
    loan_amount: float
    loan_tenure_months: int
    cibil_score: int
    active_loans_count: int
    total_overdue_amount: float
    credit_utilization_ratio: float
    existing_emi: float

class SHAPFeatureContribution(BaseModel):
    feature_name: str
    feature_value: Any
    contribution_score: float
    interpretation: str

class MLRiskPredictionResponse(BaseModel):
    risk_category: str
    risk_probability: float
    model_name: str
    dti_ratio: float
    shap_contributions: List[SHAPFeatureContribution]
    recommended_action: str

# --- Decision Engine Schemas ---
class DecisionEvaluationRequest(BaseModel):
    application_id: str

class DecisionEvaluationResponse(BaseModel):
    application_id: str
    final_decision: str
    approved_amount: float
    interest_rate: float
    monthly_emi: float
    decision_reason: str
    rule_breakdown: Dict[str, Any]
