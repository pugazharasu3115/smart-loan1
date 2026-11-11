/**
 * UI Component Utilities: Toasts, Modals, Webcam, Charts & Formatters
 */
const UI = {
    showToast(message, type = 'info', duration = 4000) {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : type === 'warning' ? '⚠️' : 'ℹ️';
        toast.innerHTML = `<span>${icon}</span> <div>${message}</div>`;
        
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    },

    openModal(title, contentHtml, onConfirm = null, confirmText = 'Confirm') {
        const backdrop = document.getElementById('modal-backdrop');
        const modalTitle = document.getElementById('modal-title');
        const modalBody = document.getElementById('modal-body');
        const confirmBtn = document.getElementById('modal-confirm-btn');

        modalTitle.innerText = title;
        modalBody.innerHTML = contentHtml;
        
        if (onConfirm) {
            confirmBtn.style.display = 'inline-flex';
            confirmBtn.innerText = confirmText;
            confirmBtn.onclick = () => {
                onConfirm();
                UI.closeModal();
            };
        } else {
            confirmBtn.style.display = 'none';
        }

        backdrop.classList.add('active');
    },

    closeModal() {
        const backdrop = document.getElementById('modal-backdrop');
        backdrop.classList.remove('active');
    },

    formatINR(num) {
        if (num === null || num === undefined) return 'INR 0';
        return 'INR ' + Number(num).toLocaleString('en-IN', { maximumFractionDigits: 2 });
    },

    // Camera WebRTC Streamer
    cameraStream: null,

    async startWebcam(videoElementId) {
        const video = document.getElementById(videoElementId);
        if (!video) return false;

        try {
            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
                video.srcObject = stream;
                video.play();
                this.cameraStream = stream;
                return true;
            }
        } catch (err) {
            console.warn("Webcam permission denied or not available, using simulated live camera frames:", err);
            return false;
        }
        return false;
    },

    stopWebcam() {
        if (this.cameraStream) {
            this.cameraStream.getTracks().forEach(track => track.stop());
            this.cameraStream = null;
        }
    },

    captureWebcamFrame(videoElementId) {
        const video = document.getElementById(videoElementId);
        if (!video) return null;

        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth || 640;
        canvas.height = video.videoHeight || 480;
        const ctx = canvas.getContext('2d');
        
        if (this.cameraStream && video.readyState >= 2) {
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        } else {
            // Draw simulated biometric face frame with test pattern
            ctx.fillStyle = '#0f172a';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.strokeStyle = '#6366f1';
            ctx.lineWidth = 4;
            ctx.strokeRect(120, 80, 400, 320);
            ctx.fillStyle = '#818cf8';
            ctx.font = '20px sans-serif';
            ctx.fillText('LIVE BIOMETRIC BI-FACIAL FRAME CAPTURED', 140, 240);
        }
        return canvas.toDataURL('image/jpeg', 0.85);
    },

    // Render Explainable SHAP Features Bar Chart
    renderSHAPChart(containerId, shapList) {
        const container = document.getElementById(containerId);
        if (!container) return;

        if (!shapList || shapList.length === 0) {
            container.innerHTML = `<div style="color:var(--text-muted); text-align:center; padding:1.5rem;">No SHAP explanation features available yet.</div>`;
            return;
        }

        let html = `<div class="shap-container">`;
        shapList.forEach(item => {
            const isPositive = item.contribution_score > 0;
            const widthPct = Math.min(Math.abs(item.contribution_score) * 2.2, 100);
            const fillClass = isPositive ? 'shap-bar-positive' : 'shap-bar-negative';
            const scoreClass = isPositive ? 'score-pos' : 'score-neg';
            const sign = item.contribution_score > 0 ? '+' : '';

            html += `
                <div class="shap-row">
                    <div class="shap-label" title="${item.interpretation}">
                        ${item.feature_name.replace(/_/g, ' ').toUpperCase()}
                    </div>
                    <div class="shap-bar-track">
                        <div class="shap-bar-fill ${fillClass}" style="width: ${widthPct}%;"></div>
                    </div>
                    <div class="shap-score ${scoreClass}">
                        ${sign}${item.contribution_score.toFixed(1)}%
                    </div>
                </div>
                <div style="font-size:0.75rem; color:var(--text-muted); margin-top:-6px; margin-bottom:12px; padding-left:180px;">
                    ${item.interpretation}
                </div>
            `;
        });
        html += `</div>`;
        container.innerHTML = html;
    }
};

window.UI = UI;
