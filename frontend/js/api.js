/**
 * Centralized Backend API Client for Smart Loan Verification System
 */
const API_BASE_URL = window.location.origin.includes('http') ? window.location.origin : 'http://127.0.0.1:8000';

const API = {
    // Auth
    async login(username, password) {
        const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        return res.json();
    },

    async register(data) {
        const res = await fetch(`${API_BASE_URL}/api/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return res.json();
    },

    async getProfile(token) {
        const res = await fetch(`${API_BASE_URL}/api/auth/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        return res.json();
    },

    // Applicant & Loan
    async saveApplicantProfile(data) {
        const res = await fetch(`${API_BASE_URL}/api/applicant/profile`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return res.json();
    },

    async getApplicant(applicantId) {
        const res = await fetch(`${API_BASE_URL}/api/applicant/${applicantId}`);
        return res.json();
    },

    async applyLoan(data) {
        const res = await fetch(`${API_BASE_URL}/api/applicant/loan-apply`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return res.json();
    },

    async getLoanDetails(applicationId) {
        const res = await fetch(`${API_BASE_URL}/api/applicant/loan/${applicationId}`);
        return res.json();
    },

    // OCR & Documents
    async getDocPresets() {
        const res = await fetch(`${API_BASE_URL}/api/ocr/sample-presets`);
        return res.json();
    },

    async processOCR(formData) {
        const res = await fetch(`${API_BASE_URL}/api/ocr/process`, {
            method: 'POST',
            body: formData
        });
        return res.json();
    },

    // Face Biometrics
    async verifyFace(applicantId, imageBase64, refImageBase64 = null) {
        const res = await fetch(`${API_BASE_URL}/api/face/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                applicant_id: applicantId,
                image_base64: imageBase64,
                reference_image_base64: refImageBase64
            })
        });
        return res.json();
    },

    // OTP
    async generateOTP(applicantId, mobile) {
        const res = await fetch(`${API_BASE_URL}/api/otp/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ applicant_id: applicantId, mobile: mobile })
        });
        return res.json();
    },

    async verifyOTP(applicantId, otp) {
        const res = await fetch(`${API_BASE_URL}/api/otp/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ applicant_id: applicantId, otp_entered: otp })
        });
        return res.json();
    },

    // CIBIL
    async getCibilRecords() {
        const res = await fetch(`${API_BASE_URL}/api/cibil/records`);
        return res.json();
    },

    async verifyCIBIL(data) {
        const res = await fetch(`${API_BASE_URL}/api/cibil/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return res.json();
    },

    // Blockchain
    async getBlockchainLedger() {
        const res = await fetch(`${API_BASE_URL}/api/blockchain/chain`);
        return res.json();
    },

    async auditBlockchain() {
        const res = await fetch(`${API_BASE_URL}/api/blockchain/audit`);
        return res.json();
    },

    async simulateTamper(blockIndex) {
        const res = await fetch(`${API_BASE_URL}/api/blockchain/tamper-demo?block_index=${blockIndex}`, {
            method: 'POST'
        });
        return res.json();
    },

    async restoreBlockchain() {
        const res = await fetch(`${API_BASE_URL}/api/blockchain/restore-demo`, {
            method: 'POST'
        });
        return res.json();
    },

    // ML & SHAP
    async predictMLRisk(data) {
        const res = await fetch(`${API_BASE_URL}/api/ml/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return res.json();
    },

    async getMLMetrics() {
        const res = await fetch(`${API_BASE_URL}/api/ml/model-metrics`);
        return res.json();
    },

    // Decision Engine
    async evaluateDecision(applicationId) {
        const res = await fetch(`${API_BASE_URL}/api/decision/evaluate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ application_id: applicationId })
        });
        return res.json();
    },

    // Admin
    async getAdminMetrics() {
        const res = await fetch(`${API_BASE_URL}/api/admin/metrics`);
        return res.json();
    },

    async getAdminApplications(status = 'ALL', search = '') {
        const res = await fetch(`${API_BASE_URL}/api/admin/applications?status_filter=${status}&search=${encodeURIComponent(search)}`);
        return res.json();
    },

    async getApplicationAudit(applicationId) {
        const res = await fetch(`${API_BASE_URL}/api/admin/application/${applicationId}/audit-trail`);
        return res.json();
    },

    async submitAdminAction(applicationId, action, notes, amount = null) {
        const res = await fetch(`${API_BASE_URL}/api/admin/application/${applicationId}/action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action: action,
                admin_notes: notes,
                approved_amount: amount
            })
        });
        return res.json();
    },

    // Real-Time Monitoring
    async getMonitoringMetrics() {
        const res = await fetch(`${API_BASE_URL}/api/monitoring/metrics`);
        return res.json();
    },

    async getMonitoringEvents(limit = 40) {
        const res = await fetch(`${API_BASE_URL}/api/monitoring/events?limit=${limit}`);
        return res.json();
    },

    async simulateMonitoringTraffic() {
        const res = await fetch(`${API_BASE_URL}/api/monitoring/simulate-traffic`, {
            method: 'POST'
        });
        return res.json();
    },

    async clearMonitoringLogs() {
        const res = await fetch(`${API_BASE_URL}/api/monitoring/clear-logs`, {
            method: 'POST'
        });
        return res.json();
    }
};

window.API = API;
