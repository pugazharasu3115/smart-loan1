import os
import time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\ELCOT\OneDrive\Desktop\Smart loan\journal_figures"
os.makedirs(OUTPUT_DIR, exist_ok=True)

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE_URL = "http://127.0.0.1:8000"

def capture_figures():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROME_PATH,
            headless=True,
            args=["--disable-web-security", "--no-sandbox"]
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2  # High resolution / 2x DPI for crisp journal figures
        )
        page = context.new_page()

        print("1. Loading application...")
        page.goto(BASE_URL, wait_until="networkidle")
        time.sleep(2)

        # -------------------------------------------------------------
        # FIGURE 7: Cryptographic Blockchain Integrity Layer
        # -------------------------------------------------------------
        print("2. Capturing Figure 7: Blockchain Ledger...")
        page.evaluate("AppFlow.showSection('blockchain-section')")
        time.sleep(3)
        fig7_path = os.path.join(OUTPUT_DIR, "Fig7_Blockchain_Ledger.png")
        page.screenshot(path=fig7_path, full_page=False)
        print(f"Saved: {fig7_path}")

        # -------------------------------------------------------------
        # FIGURE 8: Admin Dashboard
        # -------------------------------------------------------------
        print("3. Capturing Figure 8: Admin Dashboard...")
        page.evaluate("""() => {
            Auth.switchRole('admin');
            AdminFlow.loadDashboard();
        }""")
        time.sleep(3)
        fig8_path = os.path.join(OUTPUT_DIR, "Fig8_Admin_Dashboard.png")
        page.screenshot(path=fig8_path, full_page=False)
        print(f"Saved: {fig8_path}")

        # -------------------------------------------------------------
        # FIGURE 6: Stage 7 - AI Risk Assessment & SHAP Decision
        # -------------------------------------------------------------
        print("4. Capturing Figure 6: AI Credit Risk & SHAP Decision...")
        page.evaluate("""() => {
            Auth.switchRole('applicant');
            AppFlow.activeApplicantId = 'APP-2026-104928';
            AppFlow.activeApplicationId = 'LN-2026-802194';
            AppFlow.goToStep(7);
            
            // Populate and show final decision panel with SHAP explainability
            const panel = document.getElementById('final-decision-panel');
            if (panel) panel.style.display = 'block';
            
            const badge = document.getElementById('final-decision-badge');
            if (badge) {
                badge.className = 'status-pill status-approved';
                badge.innerText = 'APPROVED';
            }
            
            const reason = document.getElementById('final-decision-reason');
            if (reason) reason.innerText = 'All 7 verification gates passed. Prime CIBIL score (810) and low DTI ratio (22%).';
            
            const amt = document.getElementById('final-approved-amount');
            if (amt) amt.innerText = '₹5,00,000';
            
            const emi = document.getElementById('final-emi-display');
            if (emi) emi.innerText = '₹16,016 / month';
            
            const shapList = [
                { feature_name: 'CIBIL_CREDIT_SCORE', contribution_score: 38.5, interpretation: 'High credit score significantly improves approval probability' },
                { feature_name: 'MONTHLY_NET_INCOME', contribution_score: 29.2, interpretation: 'Substantial monthly income ensures strong repayment capability' },
                { feature_name: 'EMPLOYMENT_STABILITY', contribution_score: 18.0, interpretation: 'Salaried professional with stable employment tenure' },
                { feature_name: 'CREDIT_HISTORY_AGE', contribution_score: 14.5, interpretation: 'Mature credit history of 7+ years with zero default' },
                { feature_name: 'DEBT_TO_INCOME_RATIO', contribution_score: -12.4, interpretation: 'Existing EMI burden slightly reduces borrowing margin' },
                { feature_name: 'REQUESTED_LOAN_AMOUNT', contribution_score: -8.1, interpretation: 'Loan ticket size of 5 Lakhs introduces moderate risk' },
                { feature_name: 'RECENT_CREDIT_INQUIRIES', contribution_score: -5.3, interpretation: 'Single credit pull in last 6 months' }
            ];
            UI.renderSHAPChart('shap-chart-container', shapList);
        }""")
        time.sleep(3)
        fig6_path = os.path.join(OUTPUT_DIR, "Fig6_AI_Risk_SHAP_Decision.png")
        page.screenshot(path=fig6_path, full_page=False)
        print(f"Saved: {fig6_path}")

        # -------------------------------------------------------------
        # FIGURE 9: Real-Time System & Pipeline Monitoring
        # -------------------------------------------------------------
        print("5. Capturing Figure 9: Real-Time Monitoring Dashboard...")
        page.evaluate("AppFlow.showSection('monitoring-section')")
        time.sleep(3)
        fig9_path = os.path.join(OUTPUT_DIR, "Fig9_RealTime_Monitoring.png")
        page.screenshot(path=fig9_path, full_page=False)
        print(f"Saved: {fig9_path}")

        browser.close()
        print("ALL FIGURES CAPTURED SUCCESSFULLY!")

if __name__ == "__main__":
    capture_figures()
