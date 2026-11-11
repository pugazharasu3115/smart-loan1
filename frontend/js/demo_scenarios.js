/**
 * Interactive Automated Demo Scenarios with Normal/Readable Pacing & Narration
 */
const DemoScenarios = {
    isPaused: false,
    isRunning: false,
    stepDelayMs: 3200, // 3.2 seconds comfortable normal speed for clear viewing

    async wait(ms = null) {
        const duration = ms || this.stepDelayMs;
        const start = Date.now();
        while (Date.now() - start < duration) {
            if (!this.isRunning) return;
            while (this.isPaused) {
                await new Promise(r => setTimeout(r, 100));
            }
            await new Promise(r => setTimeout(r, 50));
        }
    },

    setNarration(badge, text) {
        const bar = document.getElementById('demo-narrator-bar');
        const badgeEl = document.getElementById('demo-step-badge');
        const textEl = document.getElementById('demo-narrator-text');

        if (bar && badgeEl && textEl) {
            bar.style.display = 'block';
            badgeEl.innerText = badge;
            textEl.innerHTML = text;
        }
    },

    hideNarration() {
        const bar = document.getElementById('demo-narrator-bar');
        if (bar) bar.style.display = 'none';
        this.isRunning = false;
        this.isPaused = false;
    },

    togglePause() {
        this.isPaused = !this.isPaused;
        const btn = document.getElementById('demo-pause-btn');
        if (btn) {
            btn.innerHTML = this.isPaused ? '▶️ Resume' : '⏸️ Pause';
            btn.className = this.isPaused ? 'btn btn-success' : 'btn btn-secondary';
        }
        UI.showToast(this.isPaused ? 'Demo Paused — Take your time to view screen' : 'Demo Resumed', 'info', 2000);
    },

    stopDemo() {
        this.isRunning = false;
        this.hideNarration();
        UI.showToast('Automated Demo Exited', 'info', 2000);
    },

    // =========================================================================
    // DEMO 1: HAPPY PATH (Priya Sharma - Prime Low-Risk Approval)
    // =========================================================================
    async runHappyPathDemo() {
        this.isRunning = true;
        this.isPaused = false;
        AppFlow.showSection('applicant-section');

        // Step 1: Pre-fill & Display Profile
        this.setNarration(
            'DEMO 1 • STEP 1 OF 7',
            'Filling Applicant Identity & KYC Profile for <strong>Priya Sharma</strong> (Income: INR 95,000/mo)...'
        );
        document.getElementById('prof-name').value = 'Priya Sharma';
        document.getElementById('prof-dob').value = '1994-06-15';
        document.getElementById('prof-mobile').value = '9876543210';
        document.getElementById('prof-email').value = 'priya.sharma@example.com';
        document.getElementById('prof-pan').value = 'ABCPS1234D';
        document.getElementById('prof-income').value = '95000';
        document.getElementById('prof-existing-emi').value = '5000';
        AppFlow.goToStep(1);

        await this.wait(3500);
        if (!this.isRunning) return;
        await AppFlow.submitProfile();

        // Step 2: Loan Amount & EMI Calculation
        this.setNarration(
            'DEMO 1 • STEP 2 OF 7',
            'Configuring Loan: <strong>INR 5,00,000</strong> for 36 Months @ 10.5% p.a. (Calculating Monthly EMI: INR 16,251)...'
        );
        document.getElementById('loan-amount-input').value = '500000';
        document.getElementById('loan-tenure-input').value = '36';
        document.getElementById('loan-purpose-input').value = 'Home Renovation';
        AppFlow.goToStep(2);

        await this.wait(3500);
        if (!this.isRunning) return;
        await AppFlow.submitLoanApplication();

        // Step 3: Document OCR & Fuzzy Levenshtein Matching
        this.setNarration(
            'DEMO 1 • STEP 3 OF 7',
            'Running Document OCR: Extracting PAN Card fields & computing Levenshtein fuzzy string correlation...'
        );
        document.getElementById('doc-type-select').value = 'PAN';
        document.getElementById('doc-preset-select').value = 'PAN_PRIYA_SHARMA';
        AppFlow.goToStep(3);

        await this.wait(2000);
        if (!this.isRunning) return;
        await AppFlow.runDocumentOCR();

        await this.wait(3500);
        if (!this.isRunning) return;

        // Step 4: Live Biometric Face Matching
        this.setNarration(
            'DEMO 1 • STEP 4 OF 7',
            'Webcam Biometric Capture: Analyzing live facial embedding descriptors against onboarding profile...'
        );
        AppFlow.goToStep(4);

        await this.wait(2500);
        if (!this.isRunning) return;
        await AppFlow.captureAndVerifyFace();

        await this.wait(3500);
        if (!this.isRunning) return;

        // Step 5: Mobile OTP (TOTP) Possession Check
        this.setNarration(
            'DEMO 1 • STEP 5 OF 7',
            'Mobile Possession Check: Generating time-based TOTP code via simulated SMS gateway...'
        );
        AppFlow.goToStep(5);

        await this.wait(2000);
        if (!this.isRunning) return;
        await AppFlow.requestOTP();

        await this.wait(3000);
        if (!this.isRunning) return;
        await AppFlow.verifyEnteredOTP();

        await this.wait(3500);
        if (!this.isRunning) return;

        // Step 6: Multi-Attribute CIBIL Credit Bureau Verification
        this.setNarration(
            'DEMO 1 • STEP 6 OF 7',
            'Querying Mock CIBIL Bureau: Correlating Name + DOB + PAN + Mobile to fetch credit score (810 Prime)...'
        );
        AppFlow.goToStep(6);

        await this.wait(2000);
        if (!this.isRunning) return;
        await AppFlow.runCIBILVerification();

        await this.wait(4000);
        if (!this.isRunning) return;

        // Step 7: Final Composite 7-Gate Decision & SHAP Explainability
        this.setNarration(
            'DEMO 1 • STEP 7 OF 7',
            'Finalizing 7-Gate Composite Decision: Running ML Gradient Boosting & generating SHAP Explainable AI Waterfall Chart...'
        );
        AppFlow.goToStep(7);

        await this.wait(2000);
        if (!this.isRunning) return;
        await AppFlow.runCompositeDecision();

        this.setNarration(
            'DEMO 1 COMPLETE ✅',
            'Loan <strong>APPROVED for INR 5,00,000</strong>! All 7 verification gates passed. SHA-256 block hash linked to blockchain ledger.'
        );
        UI.showToast('✅ Demo 1 Completed: Prime Loan Auto-Approved with Proof!', 'success', 6000);
    },

    // =========================================================================
    // DEMO 2: SAME-NAME MISMATCH / IMPERSONATION FRAUD CATCH
    // =========================================================================
    async runMismatchDemo() {
        this.isRunning = true;
        this.isPaused = false;
        AppFlow.showSection('applicant-section');

        this.setNarration(
            'DEMO 2 • STEP 1 OF 5',
            'Simulating Duplicate-Name Applicant <strong>Rajesh Kumar</strong> (DOB: 1999-11-04 vs Bureau: 1988-03-22)...'
        );

        document.getElementById('prof-name').value = 'Rajesh Kumar';
        document.getElementById('prof-dob').value = '1999-11-04';
        document.getElementById('prof-mobile').value = '9811223344';
        document.getElementById('prof-email').value = 'rajesh.kumar99@example.com';
        document.getElementById('prof-pan').value = 'XYZRK9988A';
        document.getElementById('prof-income').value = '35000';
        document.getElementById('prof-existing-emi').value = '12000';
        AppFlow.goToStep(1);

        await this.wait(3500);
        if (!this.isRunning) return;
        await AppFlow.submitProfile();

        // Loan Step
        this.setNarration(
            'DEMO 2 • STEP 2 OF 5',
            'Applying for Personal Loan of INR 4,00,000...'
        );
        document.getElementById('loan-amount-input').value = '400000';
        document.getElementById('loan-tenure-input').value = '24';
        document.getElementById('loan-purpose-input').value = 'Personal';
        AppFlow.goToStep(2);

        await this.wait(3000);
        if (!this.isRunning) return;
        await AppFlow.submitLoanApplication();

        // Document OCR
        this.setNarration(
            'DEMO 2 • STEP 3 OF 5',
            'Uploading secondary ID card for Rajesh Kumar...'
        );
        document.getElementById('doc-type-select').value = 'PAN';
        document.getElementById('doc-preset-select').value = 'PAN_IMPERSONATOR_RAJESH';
        AppFlow.goToStep(3);

        await this.wait(2000);
        if (!this.isRunning) return;
        await AppFlow.runDocumentOCR();

        await this.wait(3500);
        if (!this.isRunning) return;

        // CIBIL Multi-Attribute Mismatch Detection
        this.setNarration(
            'DEMO 2 • KEY VIVA STEP',
            'Querying CIBIL Bureau: Name matches "Rajesh Kumar", but PAN & DOB differ! Flagging <strong>POTENTIAL IMPERSONATION</strong>...'
        );
        AppFlow.goToStep(6);

        await this.wait(2000);
        if (!this.isRunning) return;
        await AppFlow.runCIBILVerification();

        await this.wait(4500);
        if (!this.isRunning) return;

        // Decision Evaluation: Routes to Manual Review
        this.setNarration(
            'DEMO 2 • FINAL DECISION',
            'Decision Engine automatically routes application to <strong>MANUAL UNDERWRITER REVIEW QUEUE</strong> (No auto-approval).'
        );
        AppFlow.goToStep(7);

        await this.wait(2000);
        if (!this.isRunning) return;
        await AppFlow.runCompositeDecision();

        this.setNarration(
            'DEMO 2 COMPLETE 🛡️',
            'Identity fraud caught: Multi-attribute correlation defense proved that same name alone is not enough for approval!'
        );
        UI.showToast('🛡️ Demo 2 Completed: Impersonation caught & held for Underwriter Review!', 'warning', 6000);
    },

    // =========================================================================
    // DEMO 3: BLOCKCHAIN CYBER-TAMPER ATTACK & DETECTION
    // =========================================================================
    async runBlockchainTamperDemo() {
        this.isRunning = true;
        this.isPaused = false;
        AppFlow.showSection('blockchain-section');

        this.setNarration(
            'DEMO 3 • STEP 1 OF 3',
            'Loading Cryptographic Blockchain Ledger (Inspecting SHA-256 Block Hashes)...'
        );
        await AppFlow.loadBlockchainLedger();

        await this.wait(3500);
        if (!this.isRunning) return;

        // Simulate Tamper
        this.setNarration(
            'DEMO 3 • STEP 2 OF 3',
            'Simulating malicious out-of-band database alteration on Block #1 (Altering verified credit score hash)...'
        );
        await API.simulateTamper(1);

        await this.wait(2000);
        if (!this.isRunning) return;
        await AppFlow.loadBlockchainLedger();

        this.setNarration(
            'DEMO 3 • TAMPER DETECTED 🚨',
            'Audit caught corrupted block: Recomputed SHA-256 hash does not match stored block hash! Integrity failure flagged.'
        );
        UI.showToast('🚨 TAMPER DETECTED: Blockchain cryptographic audit flagged corrupted block hash!', 'error', 6000);
    },

    async restoreBlockchainLedger() {
        await API.restoreBlockchain();
        await AppFlow.loadBlockchainLedger();
        this.setNarration(
            'BLOCKCHAIN RESTORED 🛠️',
            'All SHA-256 block hashes re-computed and verified. Ledger is in 100% valid cryptographic state.'
        );
        UI.showToast('Blockchain ledger restored to 100% valid state.', 'success');
    }
};

window.DemoScenarios = DemoScenarios;
