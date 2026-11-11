# Smart Loan Verification and Approval System
## Software-Only Implementation Plan

**Project:** Blockchain-Based Smart Loan Verification and Approval System with OCR, Face Authentication, CIBIL Verification, and Explainable Credit-Risk ML
**Nature:** Final-year academic prototype — 100% software, no real banking/CIBIL access, no physical hardware beyond a standard laptop + webcam.

---

## 0. Guiding Principles (apply to every phase)

- **No real financial system access.** CIBIL is a mock/simulated local database. Do not attempt to connect to real credit bureaus.
- **No physical hardware.** Face capture uses a laptop/phone webcam through the browser; OTP uses a mock SMS service or console/log-based delivery, not a paid SMS gateway (unless you want to add one later as a stretch goal).
- **Blockchain = integrity layer, not a score source.** It stores hashes of verification records, not raw sensitive data.
- **Every phase ends with a working, demoable increment** — this makes review checkpoints and your final demo much easier.
- **Sensitive data stays encrypted in a normal database; only proof hashes go on-chain.**

---

## Suggested Software Stack (concrete, free/open-source)

| Layer | Suggested Tools |
|---|---|
| Frontend | HTML/CSS/JavaScript, or React (optional) |
| Backend | Python — Flask or FastAPI |
| Database | SQLite (dev) → PostgreSQL (final submission) |
| OCR | Tesseract OCR (`pytesseract`) + OpenCV for preprocessing |
| Face Authentication | `face_recognition` (dlib-based) or OpenCV + a pretrained embedding model |
| OTP | `pyotp` (TOTP) + console/log-based "mock SMS" |
| Blockchain | Lightweight custom Python blockchain simulation (linked SHA-256 blocks in SQLite/JSON) — no need for real Hyperledger/Ethereum unless you want extra marks |
| ML | scikit-learn, XGBoost |
| Explainability | `shap` |
| Auth/Security | `bcrypt`/`passlib` for password hashing, JWT for sessions |
| API | REST (Flask-RESTful / FastAPI routers) |

---

## Phase-by-Phase Plan

### Phase 0 — Project Setup & Architecture
**Goal:** Ready-to-code environment and finalized design.
- Set up repo structure (backend, frontend, ml, blockchain, docs folders)
- Set up virtual environment, install core libraries
- Finalize DB schema (from Section 25 of your notes: applicants, documents, face_verification, otp_verification, cibil_records, blockchain_records, loan_applications)
- Create low-fidelity wireframes for the 16 screens listed in your notes
**Deliverable:** Repo skeleton + ER diagram + wireframes.

---

### Phase 1 — Core Web App: Auth & Base UI
**Goal:** Working login/register shell with routing for both portals.
- Applicant login/register (password hashing, session/JWT)
- Admin login (separate role)
- Base navigation shell for Applicant Portal and Admin Portal
**Deliverable:** Screens 1 (Login) + basic navigation.

---

### Phase 2 — Applicant Registration Module
**Goal:** Capture applicant profile and generate a unique Applicant Verification ID.
- Registration form: name, DOB, mobile, address, PAN/ID, employment info, income, loan amount, tenure
- Auto-generate `APP-YYYY-XXXXXX` ID
- Store in `applicants` table
**Deliverable:** Screen 2 (Applicant Registration) + Screen 3 (Loan Application form).

---

### Phase 3 — Document Upload & OCR Module
**Goal:** Extract structured identity data from uploaded documents.
- File upload (PAN/Aadhaar/Driving Licence/income doc — use sample/mock documents, not real IDs)
- Image preprocessing (OpenCV: grayscale, deskew, denoise)
- Text extraction (Tesseract OCR)
- Parse extracted text into structured JSON (name, DOB, ID number)
- Store in `documents` table with a document hash (for later integrity checks)
**Deliverable:** Screens 4–5 (Document Upload, OCR Result).

---

### Phase 4 — Identity Matching Module
**Goal:** Compare application data vs OCR data vs stored identity data.
- Field-by-field comparison logic (name, DOB, ID, mobile)
- Fuzzy-matching for minor OCR text variations (e.g., Levenshtein distance) so genuine matches aren't rejected over OCR noise
- Pass/Fail flag with mismatch reasons stored
**Deliverable:** Screen 6 (Identity Verification result table).

---

### Phase 5 — Face Authentication Module
**Goal:** Add face as a second identity factor.
- Face registration (capture once at onboarding)
- Live face capture at verification time (webcam via browser)
- Face embedding comparison (`face_recognition` / OpenCV DNN) → similarity score
- Store result in `face_verification` table
**Deliverable:** Screen 7 (Face Verification, e.g., "Similarity = 96%, VERIFIED").

---

### Phase 6 — OTP Verification Module
**Goal:** Confirm control of the registered mobile number.
- Generate time-based OTP (`pyotp`)
- "Send" via mock SMS (log/console/dev inbox — clearly labeled as simulated in your report)
- Verify entered OTP against generated OTP, with expiry
- Store in `otp_verification` table
**Deliverable:** Screen 8 (OTP Verification).

---

### Phase 7 — Mock CIBIL Database & Verification
**Goal:** Simulate a credit bureau lookup using multi-attribute matching (not name-only).
- Build a seeded mock `cibil_records` table (several test applicants, including deliberately duplicate names with different DOB/mobile — this sets up your key demo scenario)
- Lookup logic: match on Name + DOB + ID + Mobile + Verification ID combined, never name alone
- Return credit score, active loans, overdue amount on successful match
**Deliverable:** Screen 9 (CIBIL Verification).

---

### Phase 8 — CIBIL Mismatch Detection Logic
**Goal:** Explicitly demonstrate the "same name, different person" problem being caught.
- Build the comparison matrix (Name/DOB/ID/Mobile/Face → Match/No Match)
- Rule: Name match alone ≠ verified; all key attributes must align
- On mismatch → flag `MANUAL REVIEW / HOLD`, log reason
**Deliverable:** Screen 10 (CIBIL Mismatch Detection) — this is your strongest demo scenario, build it carefully with a clear before/after example.

---

### Phase 9 — Blockchain Integrity Module
**Goal:** Tamper-evident proof of the verification event (not the CIBIL score itself).
- Build a simple chained-block structure: each block stores `{applicant_id, cibil_control_number, credit_score_hash, timestamp, previous_hash}`
- Generate SHA-256 hash per verification event; append as a new "block" in `blockchain_records`
- Re-verification function: recompute hash from stored data and compare to blockchain-stored hash → VALID / TAMPER DETECTED
**Deliverable:** Screen 11 (Blockchain Verification) with a working "tamper detection" demo (edit a record manually and show the mismatch).

---

### Phase 10 — ML Credit Risk Model
**Goal:** Predict risk category from verified data.
- Prepare/simulate a labeled dataset (income, credit score, DTI ratio, active loans, payment history, delinquencies, credit utilization)
- Train and compare: Logistic Regression, Random Forest, Gradient Boosting/XGBoost
- Select best-performing model (Gradient Boosting is the common winner per your reference paper) and save it
- Output: risk probability + LOW/MEDIUM/HIGH category
**Deliverable:** Screen 12 (Credit Risk Prediction) + a model comparison table for your report.

---

### Phase 11 — Explainable AI (SHAP)
**Goal:** Make the ML output interpretable for a bank officer.
- Integrate SHAP with the trained model
- Generate per-applicant feature contribution values
- Render as a simple bar chart / ranked list ("Payment history +35%", etc.)
**Deliverable:** Screen 13 (SHAP Explanation).

---

### Phase 12 — Decision Engine
**Goal:** Combine everything into a final recommendation using explicit rules (not ML alone).
- Rule layer: `IF Identity=VERIFIED AND Face=VERIFIED AND OTP=VERIFIED AND CIBIL=VERIFIED AND Blockchain=VALID AND Risk=LOW → APPROVE`, with REVIEW/REJECT branches
- Store final decision + reasoning trail in `loan_applications`
**Deliverable:** Screen 14 (Loan Decision).

---

### Phase 13 — Admin Dashboard & Reporting
**Goal:** Give a bank-officer view across all applications.
- Aggregate stats (total applications, verified counts, risk distribution, manual reviews) — as in your Section 37 mockup
- Drill-down into a single applicant's full verification trail
- Screen 15 (Verification History) and Screen 16 (Admin Dashboard)
**Deliverable:** Full admin portal.

---

### Phase 14 — Security Hardening
**Goal:** Make the prototype defensible during review questions.
- Password hashing (bcrypt), session/JWT expiry
- Encrypt sensitive fields at rest (e.g., Fernet/AES for PAN-like fields in the DB)
- Confirm only hashes (never raw PAN/Aadhaar/CIBIL data) are written to the blockchain module
- Basic input validation/sanitization on all forms and API endpoints
**Deliverable:** Security checklist + short write-up for your report.

---

### Phase 15 — Integration Testing & Demo Preparation
**Goal:** One clean end-to-end flow, plus your key failure-case demo.
- Full happy-path run: Registration → OCR → Identity → Face → OTP → CIBIL → Blockchain → ML → SHAP → Decision = APPROVE
- Mismatch-case run: same name, different DOB/mobile/face → CIBIL MATCH FAILED → MANUAL REVIEW (Section 33 scenario)
- Tamper-detection run: manually alter a stored record → blockchain hash mismatch caught
- Fix bugs found during these three rehearsed runs
**Deliverable:** Three working demo scripts, screenshots/recording for backup.

---

### Phase 16 — Documentation & Final Report
**Goal:** Tie the software to your academic write-up.
- Architecture diagram, ER diagram, module descriptions
- Existing vs Proposed system comparison (Sections 29–30)
- Advantages (Section 31), Research Contribution framing (Section 38)
- Careful phrasing per Section 28 ("decision-support recommendation," not "the AI decides," etc.)
**Deliverable:** Final project report + PPT source content.

---

## Suggested Timeline (12–14 week final-year schedule)

| Weeks | Phases |
|---|---|
| 1 | Phase 0–1 (Setup, Auth/UI) |
| 2 | Phase 2 (Registration) |
| 3–4 | Phase 3–4 (OCR + Identity Matching) |
| 5 | Phase 5 (Face Authentication) |
| 6 | Phase 6 (OTP) |
| 7 | Phase 7–8 (Mock CIBIL + Mismatch Detection) |
| 8 | Phase 9 (Blockchain) |
| 9–10 | Phase 10–11 (ML + SHAP) |
| 11 | Phase 12 (Decision Engine) |
| 12 | Phase 13 (Admin Dashboard) |
| 13 | Phase 14–15 (Security, Integration Testing, Demo Rehearsal) |
| 14 | Phase 16 (Documentation/Report) |

Adjust pacing based on your actual review/submission calendar — Phases 3–11 (the core verification pipeline) are where most effort should go; Phases 0, 1, 14, 16 are comparatively light.

---

## Quick Feature Checklist (all mapped to a phase above)

- [ ] Applicant registration + unique Verification ID (Phase 2)
- [ ] Document upload + OCR extraction (Phase 3)
- [ ] Identity field matching w/ fuzzy logic (Phase 4)
- [ ] Face registration + live face match (Phase 5)
- [ ] Mobile OTP generation/verification (Phase 6)
- [ ] Mock CIBIL DB + multi-attribute lookup (Phase 7)
- [ ] CIBIL mismatch detection & hold logic (Phase 8)
- [ ] SHA-256 hashing + chained block storage (Phase 9)
- [ ] Tamper detection re-verification (Phase 9)
- [ ] ML risk model (LogReg/RF/GB comparison) (Phase 10)
- [ ] SHAP explanation output (Phase 11)
- [ ] Rule-based decision engine (Phase 12)
- [ ] Admin dashboard + per-applicant drill-down (Phase 13)
- [ ] Password hashing, field encryption, input validation (Phase 14)
- [ ] End-to-end + mismatch + tamper demo scripts (Phase 15)
- [ ] Final report & presentation content (Phase 16)
