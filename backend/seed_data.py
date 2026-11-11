import hashlib
from datetime import datetime
from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine, Base
from backend.models import User, CIBILRecord, Applicant, LoanApplication, BlockchainBlock
from backend.security import get_password_hash, encrypt_field
from backend.services.blockchain_service import BlockchainService

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 1. Seed Admin User
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@smartloan.bank.local",
                hashed_password=get_password_hash("admin123"),
                role="admin",
                full_name="Chief Credit Underwriter"
            )
            db.add(admin)

        # 2. Seed Demo Applicant User (Priya Sharma)
        priya_user = db.query(User).filter(User.username == "priya").first()
        if not priya_user:
            priya_user = User(
                username="priya",
                email="priya.sharma@example.com",
                hashed_password=get_password_hash("password123"),
                role="applicant",
                full_name="Priya Sharma"
            )
            db.add(priya_user)
            
        db.commit()

        # 3. Seed Mock CIBIL Credit Bureau Records
        cibil_profiles = [
            {
                "cibil_control_number": "CIBIL-2026-884910",
                "full_name": "Priya Sharma",
                "dob": "1994-06-15",
                "pan_number": "ABCPS1234D",
                "mobile_number": "9876543210",
                "credit_score": 810,
                "active_loans_count": 1,
                "total_active_loan_amount": 120000.0,
                "total_overdue_amount": 0.0,
                "credit_utilization_ratio": 0.18,
                "payment_history_score": 99.4,
                "delinquencies_count": 0,
                "risk_band": "PRIME"
            },
            {
                "cibil_control_number": "CIBIL-2026-773192",
                "full_name": "Rajesh Kumar",
                "dob": "1988-03-22",
                "pan_number": "BKPRK5678M",
                "mobile_number": "9822334455",
                "credit_score": 760,
                "active_loans_count": 2,
                "total_active_loan_amount": 350000.0,
                "total_overdue_amount": 0.0,
                "credit_utilization_ratio": 0.28,
                "payment_history_score": 96.0,
                "delinquencies_count": 0,
                "risk_band": "PRIME"
            },
            {
                "cibil_control_number": "CIBIL-2026-551029",
                "full_name": "Rajesh Kumar", # Duplicate Name / Impersonator Demo
                "dob": "1999-11-04",
                "pan_number": "XYZRK9988A",
                "mobile_number": "9811223344",
                "credit_score": 540,
                "active_loans_count": 4,
                "total_active_loan_amount": 620000.0,
                "total_overdue_amount": 85000.0,
                "credit_utilization_ratio": 0.88,
                "payment_history_score": 62.0,
                "delinquencies_count": 4,
                "risk_band": "HIGH_RISK"
            },
            {
                "cibil_control_number": "CIBIL-2026-663812",
                "full_name": "Amit Patel",
                "dob": "1991-09-10",
                "pan_number": "ABCPP9911X",
                "mobile_number": "9712345678",
                "credit_score": 685,
                "active_loans_count": 2,
                "total_active_loan_amount": 250000.0,
                "total_overdue_amount": 5000.0,
                "credit_utilization_ratio": 0.42,
                "payment_history_score": 88.5,
                "delinquencies_count": 1,
                "risk_band": "SUBPRIME"
            },
            {
                "cibil_control_number": "CIBIL-2026-440192",
                "full_name": "Ananya Verma",
                "dob": "1996-12-05",
                "pan_number": "DEFPA4455Z",
                "mobile_number": "9988776655",
                "credit_score": 520,
                "active_loans_count": 5,
                "total_active_loan_amount": 890000.0,
                "total_overdue_amount": 140000.0,
                "credit_utilization_ratio": 0.94,
                "payment_history_score": 52.0,
                "delinquencies_count": 6,
                "risk_band": "HIGH_RISK"
            }
        ]

        for p in cibil_profiles:
            existing = db.query(CIBILRecord).filter(CIBILRecord.cibil_control_number == p["cibil_control_number"]).first()
            if not existing:
                record = CIBILRecord(**p)
                db.add(record)
        
        db.commit()

        # 4. Seed Genesis Block in Blockchain
        BlockchainService.ensure_genesis_block(db)

        # 5. Pre-seed Sample Historical Completed Application for Demo & Admin Reporting
        priya_app_id = "APP-2026-104928"
        existing_priya = db.query(Applicant).filter(Applicant.applicant_id == priya_app_id).first()
        if not existing_priya:
            priya_applicant = Applicant(
                applicant_id=priya_app_id,
                user_id=priya_user.id if priya_user else None,
                full_name="Priya Sharma",
                dob="1994-06-15",
                mobile="9876543210",
                email="priya.sharma@example.com",
                address="Flat 402, Green Meadows, MG Road, Bengaluru",
                pan_number=encrypt_field("ABCPS1234D"),
                aadhaar_number=encrypt_field("918273645019"),
                employment_type="Salaried",
                monthly_income=95000.0,
                existing_emi=5000.0
            )
            db.add(priya_applicant)
            db.commit()

            loan_app = LoanApplication(
                application_id="LN-2026-802194",
                applicant_id=priya_app_id,
                loan_amount=500000.0,
                loan_tenure_months=36,
                loan_purpose="Home Renovation",
                interest_rate=9.5,
                monthly_emi=16016.0,
                identity_status="VERIFIED",
                face_status="VERIFIED",
                otp_status="VERIFIED",
                cibil_status="VERIFIED",
                blockchain_status="VALID",
                cibil_score=810,
                dti_ratio=0.22,
                risk_category="LOW",
                risk_probability=0.082,
                shap_explanation_json='{"cibil_score": -32.5, "dti_ratio": -18.2, "monthly_income": -14.0}',
                final_decision="APPROVED",
                decision_reason="All 7 verification gates passed. Prime CIBIL score (810) and low DTI ratio (22%).",
                approved_amount=500000.0,
                admin_notes="Auto-approved by Smart Loan Rule Engine."
            )
            db.add(loan_app)
            db.commit()

            # Add blockchain verification block for Priya
            verif_payload = {
                "applicant_id": priya_app_id,
                "identity": "VERIFIED",
                "face_similarity": 96.4,
                "otp_verified": True,
                "cibil_score": 810,
                "decision": "APPROVED"
            }
            BlockchainService.create_verification_block(
                db=db,
                applicant_id=priya_app_id,
                cibil_control_number="CIBIL-2026-884910",
                credit_score=810,
                verification_payload=verif_payload
            )

        print("Smart Loan Database Seeded Successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
