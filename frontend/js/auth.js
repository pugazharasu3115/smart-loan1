/**
 * Authentication & Session Management Module
 */
const Auth = {
    token: localStorage.getItem('smartloan_token') || null,
    currentUser: JSON.parse(localStorage.getItem('smartloan_user') || 'null'),

    init() {
        if (this.token && this.currentUser) {
            this.updateUserBadge();
        } else {
            // Default demo guest session as applicant
            this.currentUser = {
                username: 'priya',
                role: 'applicant',
                applicant_id: 'APP-2026-104928'
            };
            this.updateUserBadge();
        }
    },

    setSession(token, user) {
        this.token = token;
        this.currentUser = user;
        localStorage.setItem('smartloan_token', token);
        localStorage.setItem('smartloan_user', JSON.stringify(user));
        this.updateUserBadge();
    },

    logout() {
        this.token = null;
        this.currentUser = null;
        localStorage.removeItem('smartloan_token');
        localStorage.removeItem('smartloan_user');
        UI.showToast('Logged out successfully', 'info');
        this.showView('auth');
    },

    updateUserBadge() {
        const badge = document.getElementById('user-badge-container');
        if (!badge) return;

        if (this.currentUser) {
            badge.innerHTML = `
                <div class="user-badge">
                    <span>👤 <strong>${this.currentUser.username}</strong></span>
                    <span class="user-role role-${this.currentUser.role}">${this.currentUser.role}</span>
                </div>
            `;
        }
    },

    switchRole(targetRole) {
        if (targetRole === 'admin') {
            this.currentUser = {
                username: 'admin',
                role: 'admin',
                full_name: 'Chief Credit Underwriter'
            };
            this.updateUserBadge();
            UI.showToast('Switched to Underwriter Admin Portal', 'success');
            AppFlow.showSection('admin-section');
            AdminFlow.loadDashboard();
        } else {
            this.currentUser = {
                username: 'priya',
                role: 'applicant',
                applicant_id: 'APP-2026-104928'
            };
            this.updateUserBadge();
            UI.showToast('Switched to Applicant Portal', 'info');
            AppFlow.showSection('applicant-section');
        }
    }
};

window.Auth = Auth;
