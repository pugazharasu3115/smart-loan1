from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="applicant")  # 'applicant' or 'admin'
    full_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    applicants = relationship("Applicant", back_populates="user")

class Applicant(Base):
    __tablename__ = "applicants"

    id = Column(Integer, primary_key=True, index=True)
    applicant_id = Column(String(50), unique=True, index=True, nullable=False)  # APP-YYYY-XXXXXX
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    full_name = Column(String(255), nullable=False)
    dob = Column(String(20), nullable=False)  # YYYY-MM-DD
    mobile = Column(String(20), nullable=False)
    email = Column(String(255), nullable=False)
    address = Column(Text, nullable=True)
    pan_number = Column(String(255), nullable=False)  # Encrypted at rest
    aadhaar_number = Column(String(255), nullable=True) # Encrypted at rest
    employment_type = Column(String(100), nullable=True) # Salaried / Self-Employed
    monthly_income = Column(Float, default=0.0)
    existing_emi = Column(Float, default=0.0)
    registered_face_embedding = Column(Text, nullable=True)  # JSON-encoded array or feature vector
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="applicants")
    loans = relationship("LoanApplication", back_populates="applicant")
    documents = relationship("DocumentRecord", back_populates="applicant")
    face_verifications = relationship("FaceVerification", back_populates="applicant")
    otp_verifications = relationship("OTPVerification", back_populates="applicant")
    blockchain_blocks = relationship("BlockchainBlock", back_populates="applicant")

class LoanApplication(Base):
    __tablename__ = "loan_applications"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(String(50), unique=True, index=True, nullable=False) # LN-YYYY-XXXXXX
    applicant_id = Column(String(50), ForeignKey("applicants.applicant_id"), nullable=False)
    loan_amount = Column(Float, nullable=False)
    loan_tenure_months = Column(Integer, nullable=False)
    loan_purpose = Column(String(255), nullable=False) # Personal, Home, Auto, Education, Business
    interest_rate = Column(Float, default=10.5)
    monthly_emi = Column(Float, default=0.0)
    
    # Verification Stages Flags
    identity_status = Column(String(50), default="PENDING") # PENDING / VERIFIED / MISMATCH / FAILED
    face_status = Column(String(50), default="PENDING")     # PENDING / VERIFIED / MISMATCH / FAILED
    otp_status = Column(String(50), default="PENDING")      # PENDING / VERIFIED / FAILED
    cibil_status = Column(String(50), default="PENDING")    # PENDING / VERIFIED / MISMATCH / NOT_FOUND
    blockchain_status = Column(String(50), default="PENDING") # PENDING / VALID / TAMPER_DETECTED
    
    # Risk & ML Prediction
    cibil_score = Column(Integer, nullable=True)
    dti_ratio = Column(Float, nullable=True) # Debt to Income Ratio
    risk_category = Column(String(50), nullable=True) # LOW / MEDIUM / HIGH
    risk_probability = Column(Float, nullable=True)
    shap_explanation_json = Column(Text, nullable=True)
    
    # Final Composite Decision
    final_decision = Column(String(50), default="PENDING") # APPROVED / REJECTED / MANUAL_REVIEW
    decision_reason = Column(Text, nullable=True)
    approved_amount = Column(Float, default=0.0)
    admin_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    applicant = relationship("Applicant", back_populates="loans")

class DocumentRecord(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    applicant_id = Column(String(50), ForeignKey("applicants.applicant_id"), nullable=False)
    doc_type = Column(String(50), nullable=False) # PAN, AADHAAR, DRIVING_LICENSE, SALARY_SLIP
    file_name = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=False) # SHA-256 hash of document
    extracted_data_json = Column(Text, nullable=True)
    match_score = Column(Float, default=0.0)
    is_verified = Column(Boolean, default=False)
    mismatch_reasons = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    applicant = relationship("Applicant", back_populates="documents")

class FaceVerification(Base):
    __tablename__ = "face_verifications"

    id = Column(Integer, primary_key=True, index=True)
    applicant_id = Column(String(50), ForeignKey("applicants.applicant_id"), nullable=False)
    registered_face_hash = Column(String(64), nullable=True)
    live_face_hash = Column(String(64), nullable=True)
    similarity_score = Column(Float, nullable=False)
    threshold = Column(Float, default=80.0)
    is_matched = Column(Boolean, default=False)
    verification_method = Column(String(100), default="OpenCV_Biometric_Embedding")
    created_at = Column(DateTime, default=datetime.utcnow)

    applicant = relationship("Applicant", back_populates="face_verifications")

class OTPVerification(Base):
    __tablename__ = "otp_verifications"

    id = Column(Integer, primary_key=True, index=True)
    applicant_id = Column(String(50), ForeignKey("applicants.applicant_id"), nullable=False)
    mobile_number = Column(String(20), nullable=False)
    secret_key = Column(String(64), nullable=False)
    generated_otp = Column(String(10), nullable=False)
    is_verified = Column(Boolean, default=False)
    attempts = Column(Integer, default=0)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    applicant = relationship("Applicant", back_populates="otp_verifications")

class CIBILRecord(Base):
    __tablename__ = "cibil_records"

    id = Column(Integer, primary_key=True, index=True)
    cibil_control_number = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    dob = Column(String(20), nullable=False)
    pan_number = Column(String(50), index=True, nullable=False)
    mobile_number = Column(String(20), nullable=False)
    credit_score = Column(Integer, nullable=False)
    active_loans_count = Column(Integer, default=0)
    total_active_loan_amount = Column(Float, default=0.0)
    total_overdue_amount = Column(Float, default=0.0)
    credit_utilization_ratio = Column(Float, default=0.25)
    payment_history_score = Column(Float, default=95.0) # 0 to 100% on-time payments
    delinquencies_count = Column(Integer, default=0)
    risk_band = Column(String(50), default="PRIME") # PRIME / SUBPRIME / HIGH_RISK
    last_updated = Column(DateTime, default=datetime.utcnow)

class BlockchainBlock(Base):
    __tablename__ = "blockchain_records"

    id = Column(Integer, primary_key=True, index=True)
    block_index = Column(Integer, unique=True, index=True, nullable=False)
    previous_hash = Column(String(64), nullable=False)
    block_hash = Column(String(64), unique=True, index=True, nullable=False)
    applicant_id = Column(String(50), ForeignKey("applicants.applicant_id"), nullable=False)
    cibil_control_number = Column(String(50), nullable=False)
    credit_score_hash = Column(String(64), nullable=False)
    verification_data_hash = Column(String(64), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    nonce = Column(Integer, default=0)
    is_valid = Column(Boolean, default=True)

    applicant = relationship("Applicant", back_populates="blockchain_blocks")
