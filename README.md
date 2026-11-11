# Smart Loan Verification and Approval System

> **Academic Final-Year Prototype**: A 100% software-based, zero-cost loan verification and decision system integrating **Document OCR**, **Biometric Facial Matching**, **Multi-Attribute CIBIL Credit Bureau Verification**, **SHA-256 Chained Blockchain Integrity**, and **Explainable Credit Risk Machine Learning (SHAP)**.

---

## 🌟 Key Features

1. **Dual Portals (Applicant & Bank Underwriter Admin)**:
   - **Applicant Portal**: Profile creation with unique Verification ID (`APP-YYYY-XXXXXX`), Document OCR upload, Live Webcam facial capture, TOTP SMS simulation, and real-time loan tracker.
   - **Admin Command Center**: Real-time KPI summaries, risk category distributions, searchable application queue, and deep audit trail inspector with manual approve/reject actions.
2. **7-Gate Verification & Decision Engine**:
   - **Gate 1: Document OCR**: Preprocessing, regex parsing, and Levenshtein fuzzy string matching.
   - **Gate 2: Face Biometrics**: Live webcam frame feature extraction and cosine similarity scoring.
   - **Gate 3: Mobile TOTP**: Time-based one-time password possession verification.
   - **Gate 4: Multi-Attribute CIBIL Bureau**: Correlation matrix checking `Name + DOB + PAN + Mobile` to catch same-name fraud attempts.
   - **Gate 5: SHA-256 Blockchain Ledger**: Chained block hash auditing with instant tamper detection.
   - **Gate 6: ML Credit Risk Model**: Gradient Boosting risk probability prediction.
   - **Gate 7: Solvency & DTI**: Debt-to-income solvency validation.
3. **Explainable AI (SHAP)**:
   - Visual feature contribution breakdown showing exact positive and negative drivers of credit decisions.
4. **Built-In 1-Click Interactive Demo Modes**:
   - 🚀 **Demo 1: Happy Path (Priya Sharma)** — Auto-verifies and approves standard prime applicant.
   - ⚠️ **Demo 2: Same-Name Impersonation Catch (Rajesh Kumar)** — Proves that duplicate names with different DOB/PAN are flagged for Underwriter Review.
   - 🛡️ **Demo 3: Blockchain Tamper Attack & Detection** — Demonstrates hash mismatch when a stored record is tampered with.

---

## 🛠️ Tech Stack

- **Backend**: Python FastAPI, SQLAlchemy (SQLite database), Uvicorn.
- **Machine Learning**: `scikit-learn` (Gradient Boosting, Random Forest, Logistic Regression), NumPy, Pandas.
- **Explainability**: SHAP feature attribution algorithm.
- **Security & Integrity**: Custom SHA-256 linked blockchain, bcrypt password hashing, AES/Fernet field-level encryption, `pyotp` TOTP.
- **Frontend**: Modern, responsive, glassmorphic UI using Vanilla HTML5, CSS3, and ES6 JavaScript with WebRTC live webcam streaming.

---

## 🚀 How to Run Locally

### 1. Launch Server
In your terminal, simply run:
```bash
py run.py
```
Or:
```bash
python run.py
```

### 2. Access Web Application
- **Web Application**: Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.
- **Interactive Swagger API Docs**: Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

---

## 👥 Default Demo Credentials

- **Admin / Underwriter Account**:
  - Username: `admin`
  - Password: `admin123`
- **Applicant Account (Priya Sharma)**:
  - Username: `priya`
  - Password: `password123`
  - Verification ID: `APP-2026-104928`
