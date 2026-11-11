import requests
import time
import json
import os

os.environ["PYTHONIOENCODING"] = "utf-8"

BASE_URL = "http://127.0.0.1:8000"

def test_all_flows():
    print("\n--- [TEST 1] HEALTH & ROOT ENDPOINT ---")
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200, f"Health check failed: {r.text}"
    print(f"[PASS] Health Check Passed: {r.json()}")

    print("\n--- [TEST 2] AUTHENTICATION & LOGIN ---")
    login_res = requests.post(f"{BASE_URL}/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert login_res.status_code == 200, f"Admin login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    print(f"[PASS] Admin Login Successful, Token acquired: {token[:20]}...")

    print("\n--- [TEST 3] APPLICANT PROFILE REGISTRATION ---")
    applicant_payload = {
        "full_name": "Priya Sharma",
        "dob": "1994-06-15",
        "mobile": "9876543210",
        "email": "priya.sharma@example.com",
        "address": "Flat 402, Green Meadows, Bengaluru",
        "pan_number": "ABCPS1234D",
        "aadhaar_number": "918273645019",
        "employment_type": "Salaried",
        "monthly_income": 95000.0,
        "existing_emi": 5000.0
    }
    app_res = requests.post(f"{BASE_URL}/api/applicant/profile", json=applicant_payload)
    assert app_res.status_code == 200, f"Profile creation failed: {app_res.text}"
    applicant_id = app_res.json()["applicant_id"]
    print(f"[PASS] Applicant Profile Created: {applicant_id}")

    print("\n--- [TEST 4] LOAN APPLICATION SUBMISSION ---")
    loan_payload = {
        "applicant_id": applicant_id,
        "loan_amount": 500000.0,
        "loan_tenure_months": 36,
        "loan_purpose": "Home Renovation"
    }
    loan_res = requests.post(f"{BASE_URL}/api/applicant/loan-apply", json=loan_payload)
    assert loan_res.status_code == 200, f"Loan creation failed: {loan_res.text}"
    application_id = loan_res.json()["application_id"]
    print(f"[PASS] Loan Application Created: {application_id}, Monthly EMI: INR {loan_res.json()['monthly_emi']}")

    print("\n--- [TEST 5] DOCUMENT OCR & FUZZY IDENTITY MATCHING ---")
    ocr_res = requests.post(
        f"{BASE_URL}/api/ocr/process",
        data={"applicant_id": applicant_id, "doc_type": "PAN", "preset_key": "PAN_PRIYA_SHARMA"}
    )
    assert ocr_res.status_code == 200, f"OCR processing failed: {ocr_res.text}"
    ocr_data = ocr_res.json()
    assert ocr_data["is_verified"] == True, "Expected OCR verification to pass"
    print(f"[PASS] OCR Document Verified, Fuzzy Match Score: {ocr_data['match_score']}%")

    print("\n--- [TEST 6] LIVE BIOMETRIC FACE AUTHENTICATION ---")
    face_res = requests.post(
        f"{BASE_URL}/api/face/verify",
        json={"applicant_id": applicant_id, "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRg=="}
    )
    assert face_res.status_code == 200, f"Face verification failed: {face_res.text}"
    face_data = face_res.json()
    assert face_data["is_matched"] == True
    print(f"[PASS] Face Biometric Match Successful: {face_data['similarity_score']}%")

    print("\n--- [TEST 7] MOBILE TOTP VERIFICATION ---")
    otp_gen = requests.post(f"{BASE_URL}/api/otp/generate", json={"applicant_id": applicant_id, "mobile": "9876543210"})
    assert otp_gen.status_code == 200
    sim_otp = otp_gen.json()["simulated_otp"]
    print(f"Generated TOTP: {sim_otp}")
    
    otp_verif = requests.post(f"{BASE_URL}/api/otp/verify", json={"applicant_id": applicant_id, "otp_entered": sim_otp})
    assert otp_verif.status_code == 200
    assert otp_verif.json()["is_verified"] == True
    print("[PASS] TOTP Possession Verified Successfully")

    print("\n--- [TEST 8] MOCK CIBIL MULTI-ATTRIBUTE LOOKUP ---")
    cibil_res = requests.post(f"{BASE_URL}/api/cibil/verify", json={
        "applicant_id": applicant_id,
        "full_name": "Priya Sharma",
        "dob": "1994-06-15",
        "pan_number": "ABCPS1234D",
        "mobile": "9876543210"
    })
    assert cibil_res.status_code == 200
    cibil_data = cibil_res.json()
    assert cibil_data["is_verified"] == True
    print(f"[PASS] CIBIL Bureau Verified! Score: {cibil_data['credit_score']}, Control No: {cibil_data['cibil_control_number']}")

    print("\n--- [TEST 9] COMPOSITE 7-GATE DECISION & SHAP EXPLAINABILITY ---")
    dec_res = requests.post(f"{BASE_URL}/api/decision/evaluate", json={"application_id": application_id})
    assert dec_res.status_code == 200
    dec_data = dec_res.json()
    assert dec_data["final_decision"] == "APPROVED", f"Expected APPROVED, got {dec_data['final_decision']}"
    print(f"[PASS] Final Decision: {dec_data['final_decision']}, Sanctioned: INR {dec_data['approved_amount']:,.0f}")
    print(f"Decision Reason: {dec_data['decision_reason']}")

    print("\n--- [TEST 10] BLOCKCHAIN INTEGRITY & AUDIT ---")
    audit_res = requests.get(f"{BASE_URL}/api/blockchain/audit")
    assert audit_res.status_code == 200
    audit_data = audit_res.json()
    assert audit_data["is_chain_valid"] == True
    print(f"[PASS] Blockchain Audit Passed: {audit_data['audit_report']} ({audit_data['total_blocks']} Blocks)")

    print("\n--- [TEST 11] BLOCKCHAIN TAMPER DETECTION DEMO ---")
    tamper_res = requests.post(f"{BASE_URL}/api/blockchain/tamper-demo?block_index=1")
    assert tamper_res.status_code == 200
    t_data = tamper_res.json()
    assert t_data["is_chain_valid"] == False
    print(f"[PASS] Tamper Attack Successfully Caught: {t_data['audit_report']}")

    # Restore blockchain
    restore_res = requests.post(f"{BASE_URL}/api/blockchain/restore-demo")
    assert restore_res.status_code == 200
    print("[PASS] Blockchain Restored to Valid State")

    print("\n--- [TEST 12] ADMIN DASHBOARD METRICS ---")
    admin_metrics = requests.get(f"{BASE_URL}/api/admin/metrics")
    assert admin_metrics.status_code == 200
    print(f"[PASS] Admin KPIs: {admin_metrics.json()['summary']}")

    print("\n--- [TEST 13] REAL-TIME MONITORING TELEMETRY & SIMULATION ---")
    mon_res = requests.get(f"{BASE_URL}/api/monitoring/metrics")
    assert mon_res.status_code == 200
    mon_data = mon_res.json()
    assert mon_data["system_status"] == "ONLINE"
    print(f"[PASS] Real-Time Telemetry: Uptime {mon_data['uptime_formatted']}, Events Buffered: {len(mon_data['recent_events'])}")

    sim_res = requests.post(f"{BASE_URL}/api/monitoring/simulate-traffic")
    assert sim_res.status_code == 200
    assert sim_res.json()["success"] == True
    print(f"[PASS] Real-Time Pipeline Stream Simulation: {sim_res.json()['details']}")

    print("\n==================================================================")
    print("SUCCESS: ALL 13 INTEGRATION TESTS PASSED 100%!")
    print("==================================================================")

if __name__ == "__main__":
    test_all_flows()
