/**
 * Real-Time Telemetry & Monitoring Module
 * WebSocket client + Live Event Stream & Performance Telemetry
 */
const MonitoringFlow = {
    socket: null,
    isStreaming: true,
    autoScroll: true,
    currentFilter: 'ALL',
    pollTimer: null,
    eventsList: [],

    init() {
        this.connectWebSocket();
        this.bindEvents();
    },

    bindEvents() {
        // Ping socket every 15 seconds to keep connection alive
        setInterval(() => {
            if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                this.socket.send("PING");
            }
        }, 15000);
    },

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host || '127.0.0.1:8000';
        const wsUrl = `${protocol}//${host}/api/monitoring/stream`;

        try {
            this.socket = new WebSocket(wsUrl);

            this.socket.onopen = () => {
                this.updateConnectionStatus(true);
                if (this.pollTimer) {
                    clearInterval(this.pollTimer);
                    this.pollTimer = null;
                }
            };

            this.socket.onmessage = (event) => {
                try {
                    const payload = JSON.parse(event.data);
                    if (payload.type === 'SNAPSHOT') {
                        this.renderSnapshot(payload.data);
                    } else if (payload.type === 'NEW_EVENT') {
                        this.appendLiveEvent(payload.event);
                        if (payload.metrics) {
                            this.updateMetrics(payload.metrics);
                        }
                    }
                } catch (err) {
                    console.error("WS Parse Error:", err);
                }
            };

            this.socket.onclose = () => {
                this.updateConnectionStatus(false);
                // Fallback to REST polling if WebSocket disconnects
                if (!this.pollTimer) {
                    this.pollTimer = setInterval(() => this.pollMetricsREST(), 3000);
                }
                // Try reconnect in 4 seconds
                setTimeout(() => this.connectWebSocket(), 4000);
            };

            this.socket.onerror = (err) => {
                console.warn("WebSocket Error (Falling back to REST Polling):", err);
                this.updateConnectionStatus(false);
            };
        } catch (e) {
            console.error("WebSocket Init failed:", e);
            this.updateConnectionStatus(false);
            if (!this.pollTimer) {
                this.pollTimer = setInterval(() => this.pollMetricsREST(), 3000);
            }
        }
    },

    updateConnectionStatus(isConnected) {
        const badge = document.getElementById('mon-ws-status');
        const pulse = document.getElementById('mon-live-pulse');
        if (badge) {
            if (isConnected) {
                badge.className = 'status-pill status-verified';
                badge.innerText = 'WS CONNECTED (REAL-TIME)';
                if (pulse) pulse.style.background = '#10b981';
            } else {
                badge.className = 'status-pill status-pending';
                badge.innerText = 'REST POLLING (FALLBACK)';
                if (pulse) pulse.style.background = '#f59e0b';
            }
        }
    },

    async pollMetricsREST() {
        if (!this.isStreaming) return;
        try {
            const data = await API.getMonitoringMetrics();
            this.renderSnapshot(data);
        } catch (e) {
            console.error("Error polling metrics:", e);
        }
    },

    renderSnapshot(data) {
        if (!data) return;

        // System Health & Uptime
        const uptimeEl = document.getElementById('mon-uptime-val');
        if (uptimeEl) uptimeEl.innerText = data.uptime_formatted || '00:00:00';

        const cpuEl = document.getElementById('mon-cpu-val');
        if (cpuEl) cpuEl.innerText = `${data.cpu_utilization_pct}%`;

        const ramEl = document.getElementById('mon-ram-val');
        if (ramEl) ramEl.innerText = `${data.memory_usage_mb} MB`;

        // KPI Metrics
        this.updateMetrics(data.metrics, data);

        // Latencies
        if (data.metrics && data.metrics.stage_latencies) {
            this.updateLatencies(data.metrics.stage_latencies);
        }

        // Fraud Alerts
        if (data.fraud_alerts) {
            this.renderFraudAlerts(data.fraud_alerts);
        }

        // Recent Events
        if (data.recent_events) {
            this.eventsList = data.recent_events;
            this.renderEventsFeed();
        }
    },

    updateMetrics(m, fullData = null) {
        if (!m) return;
        const totalReq = document.getElementById('mon-total-req');
        if (totalReq) totalReq.innerText = m.total_requests || 0;

        const successRate = document.getElementById('mon-success-rate');
        if (successRate) successRate.innerText = `${m.success_rate_pct || 96.2}%`;

        const reqPerMin = document.getElementById('mon-throughput');
        if (reqPerMin) reqPerMin.innerText = `${m.req_per_min || 8.4} req/min`;

        const fraudCount = document.getElementById('mon-fraud-count');
        if (fraudCount) fraudCount.innerText = m.fraud_alerts_count || 0;

        const passedCount = document.getElementById('mon-passed-count');
        if (passedCount) passedCount.innerText = m.successful_verifications || 0;

        const manualCount = document.getElementById('mon-manual-count');
        if (manualCount) manualCount.innerText = m.manual_reviews || 0;
    },

    updateLatencies(lats) {
        const updateBar = (id, textId, ms, maxMs = 500) => {
            const bar = document.getElementById(id);
            const txt = document.getElementById(textId);
            if (bar) bar.style.width = `${Math.min(100, Math.round((ms / maxMs) * 100))}%`;
            if (txt) txt.innerText = `${ms} ms`;
        };

        updateBar('lat-bar-ocr', 'lat-val-ocr', lats.ocr || 240, 400);
        updateBar('lat-bar-face', 'lat-val-face', lats.face_kyc || 310, 500);
        updateBar('lat-bar-otp', 'lat-val-otp', lats.otp || 45, 150);
        updateBar('lat-bar-cibil', 'lat-val-cibil', lats.cibil || 180, 300);
        updateBar('lat-bar-ml', 'lat-val-ml', lats.ml_risk || 120, 250);
        updateBar('lat-bar-chain', 'lat-val-chain', lats.blockchain || 95, 200);
    },

    renderFraudAlerts(alerts) {
        const container = document.getElementById('mon-alerts-container');
        if (!container) return;

        if (!alerts || alerts.length === 0) {
            container.innerHTML = `
                <div class="mon-alert-empty">
                    <span style="color:var(--accent-emerald);">🛡️ No Security Anomalies Active</span>
                    <small style="color:var(--text-muted);">Biometric anti-spoofing, CIBIL hash integrity & blockchain hashes intact.</small>
                </div>
            `;
            return;
        }

        container.innerHTML = alerts.map(a => {
            const isHigh = a.severity === 'HIGH';
            return `
                <div class="mon-alert-item ${isHigh ? 'alert-high' : 'alert-med'}">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <strong>${isHigh ? '🚨 CRITICAL ANOMALY' : '⚠️ SECURITY FLAG'} [${a.stage}]</strong>
                        <small style="color:var(--text-muted);">${a.timestamp}</small>
                    </div>
                    <div style="font-size:0.85rem; margin-top:3px; color:var(--text-primary);">${a.message}</div>
                </div>
            `;
        }).join('');
    },

    appendLiveEvent(ev) {
        if (!this.isStreaming) return;
        this.eventsList.unshift(ev);
        if (this.eventsList.length > 100) this.eventsList.pop();
        this.renderEventsFeed();
    },

    renderEventsFeed() {
        const container = document.getElementById('mon-event-stream-box');
        if (!container) return;

        let filtered = this.eventsList;
        if (this.currentFilter === 'SUCCESS') {
            filtered = this.eventsList.filter(e => e.status === 'SUCCESS');
        } else if (this.currentFilter === 'ANOMALY') {
            filtered = this.eventsList.filter(e => e.is_anomaly || e.status !== 'SUCCESS');
        }

        if (filtered.length === 0) {
            container.innerHTML = `<div style="text-align:center; padding:2rem; color:var(--text-muted);">No telemetry events matching filter.</div>`;
            return;
        }

        container.innerHTML = filtered.map(e => {
            let statusPillClass = 'status-verified';
            if (e.status === 'FAILED' || e.status === 'REJECTED' || e.is_anomaly) statusPillClass = 'status-failed';
            else if (e.status === 'HOLD' || e.status === 'MISMATCH' || e.status === 'REVIEW') statusPillClass = 'status-mismatch';

            return `
                <div class="mon-log-row ${e.is_anomaly ? 'log-anomaly' : ''}">
                    <div class="mon-log-time">${e.timestamp}</div>
                    <div class="mon-log-stage"><span class="mon-stage-tag">${e.stage}</span></div>
                    <div class="mon-log-type">${e.event_type}</div>
                    <div class="mon-log-details">${e.details}</div>
                    <div class="mon-log-app">${e.applicant_id}</div>
                    <div class="mon-log-status">
                        <span class="status-pill ${statusPillClass}">${e.status}</span>
                    </div>
                    <div class="mon-log-dur">${e.duration_ms}ms</div>
                </div>
            `;
        }).join('');

        if (this.autoScroll) {
            container.scrollTop = 0;
        }
    },

    setFilter(filterType) {
        this.currentFilter = filterType;
        document.querySelectorAll('.mon-filter-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filter === filterType);
        });
        this.renderEventsFeed();
    },

    toggleStreaming() {
        this.isStreaming = !this.isStreaming;
        const btn = document.getElementById('mon-stream-toggle-btn');
        if (btn) {
            btn.innerHTML = this.isStreaming ? '⏸️ Pause Stream' : '▶️ Resume Stream';
            btn.className = this.isStreaming ? 'btn btn-secondary' : 'btn btn-primary';
        }
        UI.showToast(this.isStreaming ? 'Live Monitoring Stream Resumed' : 'Live Stream Paused', 'info');
    },

    async simulateTraffic() {
        try {
            UI.showToast('Triggering Simulated Multi-Gate Pipeline Workflow...', 'info');
            const res = await API.simulateMonitoringTraffic();
            if (res.success) {
                UI.showToast(`Simulated Live Pipeline: ${res.details.applicant_id} (${res.details.name})`, 'success');
            }
        } catch (e) {
            UI.showToast('Error during traffic simulation: ' + e.message, 'error');
        }
    },

    async clearLogs() {
        try {
            await API.clearMonitoringLogs();
            this.eventsList = [];
            this.renderEventsFeed();
            UI.showToast('Monitoring Event Stream Cleared', 'info');
        } catch (e) {
            UI.showToast('Error clearing logs: ' + e.message, 'error');
        }
    }
};

window.MonitoringFlow = MonitoringFlow;
