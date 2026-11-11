/**
 * Bank Officer & Underwriter Admin Dashboard Module
 */
const AdminFlow = {
    selectedApplicationId: null,

    async loadDashboard() {
        await Promise.all([
            this.loadMetrics(),
            this.loadApplications('ALL')
        ]);
    },

    async loadMetrics() {
        try {
            const data = await API.getAdminMetrics();
            const s = data.summary;
            const r = data.risk_distribution;

            document.getElementById('kpi-total-apps').innerText = s.total_applications;
            document.getElementById('kpi-approved-apps').innerText = s.approved;
            document.getElementById('kpi-review-apps').innerText = s.manual_review_queue;
            document.getElementById('kpi-sanctioned-amt').innerText = UI.formatINR(s.total_sanctioned_amount);
            document.getElementById('kpi-approval-rate').innerText = `${s.approval_rate}%`;
            document.getElementById('kpi-avg-cibil').innerText = s.avg_cibil_score;

            // Risk badges
            document.getElementById('risk-low-count').innerText = `${r.low_risk} Low Risk`;
            document.getElementById('risk-med-count').innerText = `${r.medium_risk} Medium Risk`;
            document.getElementById('risk-high-count').innerText = `${r.high_risk} High Risk`;
        } catch (e) {
            console.error("Error loading admin metrics:", e);
        }
    },

    async loadApplications(statusFilter = 'ALL') {
        const searchInput = document.getElementById('admin-search-input');
        const search = searchInput ? searchInput.value.trim() : '';

        try {
            const apps = await API.getAdminApplications(statusFilter, search);
            const tbody = document.getElementById('admin-apps-tbody');
            if (!tbody) return;

            tbody.innerHTML = '';
            if (apps.length === 0) {
                tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:2rem; color:var(--text-muted);">No applications found.</td></tr>`;
                return;
            }

            apps.forEach(app => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>${app.application_id}</strong><br><small style="color:var(--text-muted);">${app.created_at}</small></td>
                    <td><strong>${app.applicant_name}</strong><br><small style="color:var(--text-muted);">${app.applicant_id}</small></td>
                    <td><strong>${UI.formatINR(app.loan_amount)}</strong><br><small style="color:var(--text-muted);">${app.tenure_months} Mo @ 10.5%</small></td>
                    <td><span class="status-pill status-${(app.cibil_status || 'pending').toLowerCase()}">${app.cibil_score || 'N/A'} (${app.cibil_status})</span></td>
                    <td><span class="status-pill status-${(app.risk_category || 'pending').toLowerCase()}">${app.risk_category}</span></td>
                    <td><span class="status-pill status-${(app.blockchain_status || 'pending').toLowerCase()}">${app.blockchain_status}</span></td>
                    <td><span class="status-pill status-${app.final_decision.toLowerCase()}">${app.final_decision}</span></td>
                    <td>
                        <button class="btn btn-secondary" style="padding:0.35rem 0.75rem; font-size:0.8rem;" onclick="AdminFlow.inspectApplication('${app.application_id}')">
                            🔍 Inspect Trail
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        } catch (e) {
            console.error("Error loading applications list:", e);
        }
    },

    async inspectApplication(applicationId) {
        this.selectedApplicationId = applicationId;
        try {
            const data = await API.getApplicationAudit(applicationId);
            const app = data.application;
            const applicant = data.applicant;
            const st = data.verification_stages;

            const modalHtml = `
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:1.5rem;">
                    <div>
                        <h3>${applicant.full_name} (${applicant.applicant_id})</h3>
                        <p style="color:var(--text-secondary); font-size:0.85rem;">Application ID: <strong>${app.application_id}</strong> | Applied Amount: <strong>${UI.formatINR(app.loan_amount)}</strong></p>
                    </div>
                    <span class="status-pill status-${app.final_decision.toLowerCase()}">${app.final_decision}</span>
                </div>

                <div class="gates-grid" style="grid-template-columns: repeat(2, 1fr); margin-bottom:1.5rem;">
                    <div class="gate-card ${st.identity_ocr.status === 'VERIFIED' ? 'passed' : 'flagged'}">
                        <div class="gate-header"><span class="gate-title">1. Document OCR & Identity</span><span class="status-pill status-${st.identity_ocr.status.toLowerCase()}">${st.identity_ocr.status}</span></div>
                        <p class="gate-desc">${st.identity_ocr.documents_count} Verified Documents on record.</p>
                    </div>
                    <div class="gate-card ${st.face_biometrics.status === 'VERIFIED' ? 'passed' : 'flagged'}">
                        <div class="gate-header"><span class="gate-title">2. Live Facial Biometrics</span><span class="status-pill status-${st.face_biometrics.status.toLowerCase()}">${st.face_biometrics.status}</span></div>
                        <p class="gate-desc">Biometric Facial Embedding correlation verified.</p>
                    </div>
                    <div class="gate-card ${st.cibil_verification.status === 'VERIFIED' ? 'passed' : 'flagged'}">
                        <div class="gate-header"><span class="gate-title">3. Multi-Attribute CIBIL</span><span class="status-pill status-${st.cibil_verification.status.toLowerCase()}">${st.cibil_verification.status}</span></div>
                        <p class="gate-desc">Bureau Score: <strong>${st.cibil_verification.credit_score || 'N/A'}</strong></p>
                    </div>
                    <div class="gate-card ${st.blockchain_record.status === 'VALID' ? 'passed' : 'flagged'}">
                        <div class="gate-header"><span class="gate-title">4. Blockchain Proof</span><span class="status-pill status-${st.blockchain_record.status.toLowerCase()}">${st.blockchain_record.status}</span></div>
                        <p class="gate-desc">Block Index: #${st.blockchain_record.block_index || '0'}</p>
                    </div>
                </div>

                <div style="background:rgba(0,0,0,0.3); padding:1rem; border-radius:8px; margin-bottom:1.5rem;">
                    <strong>Decision Reason Trail:</strong>
                    <p style="color:var(--text-secondary); margin-top:4px; font-size:0.9rem;">${app.decision_reason || 'No decision trail recorded yet.'}</p>
                    ${app.admin_notes ? `<p style="color:var(--accent-indigo-light); margin-top:8px; font-size:0.85rem;"><strong>Underwriter Notes:</strong> ${app.admin_notes}</p>` : ''}
                </div>

                <div style="border-top:1px solid var(--border-color); padding-top:1.25rem;">
                    <h4 style="margin-bottom:0.75rem;">Underwriter Manual Override / Action</h4>
                    <div class="form-group" style="margin-bottom:1rem;">
                        <label>Underwriter Decision Notes / Justification:</label>
                        <input type="text" id="admin-action-notes" placeholder="Enter reason for approval or rejection..." value="Reviewed applicant KYC & risk profile.">
                    </div>
                    <div style="display:flex; gap:1rem;">
                        <button class="btn btn-success" onclick="AdminFlow.executeAction('APPROVED')">✅ Approve Application</button>
                        <button class="btn btn-danger" onclick="AdminFlow.executeAction('REJECTED')">❌ Reject Application</button>
                    </div>
                </div>
            `;

            UI.openModal(`Application Audit: ${applicationId}`, modalHtml);
        } catch (e) {
            UI.showToast('Error inspecting application audit: ' + e.message, 'error');
        }
    },

    async executeAction(actionType) {
        const notes = document.getElementById('admin-action-notes').value.trim();
        try {
            const res = await API.submitAdminAction(this.selectedApplicationId, actionType, notes);
            if (res.success) {
                UI.showToast(`Application ${this.selectedApplicationId} updated to ${actionType}`, 'success');
                UI.closeModal();
                this.loadDashboard();
            }
        } catch (e) {
            UI.showToast('Error updating application: ' + e.message, 'error');
        }
    }
};

window.AdminFlow = AdminFlow;
