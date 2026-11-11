import asyncio
import time
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import WebSocket

class MonitoringService:
    def __init__(self):
        self.start_time = time.time()
        self.active_connections: List[WebSocket] = []
        self.events_buffer: List[Dict[str, Any]] = []
        self.max_buffer_size = 200
        
        # Metric accumulators
        self.metrics = {
            "total_requests": 0,
            "successful_verifications": 0,
            "failed_verifications": 0,
            "manual_reviews": 0,
            "stage_latencies": {
                "ocr": 240,         # ms
                "face_kyc": 310,     # ms
                "otp": 45,           # ms
                "cibil": 180,        # ms
                "ml_risk": 120,      # ms
                "blockchain": 95     # ms
            },
            "fraud_alerts_count": 0,
            "active_sessions": 3
        }

        self.fraud_alerts: List[Dict[str, Any]] = [
            {
                "id": "ALT-101",
                "timestamp": datetime.utcnow().strftime("%H:%M:%S"),
                "severity": "LOW",
                "stage": "CIBIL",
                "message": "Subprime score band (540) flagged for strict collateral audit."
            }
        ]

        # Seed with initial realistic events
        self._seed_initial_events()

    def _seed_initial_events(self):
        sample_events = [
            ("SYSTEM", "BOOT", "SUCCESS", "FastAPI Core & Uvicorn ASGI Server Initialized", "SYSTEM", 15),
            ("DATABASE", "CONNECT", "SUCCESS", "SQLite Connection Pool verified (smart_loan.db)", "SYSTEM", 8),
            ("BLOCKCHAIN", "GENESIS_CHECK", "SUCCESS", "Genesis Block #0 verified (SHA-256)", "SYSTEM", 12),
            ("ML_ENGINE", "MODEL_LOAD", "SUCCESS", "GradientBoosting & RandomForest models online", "SYSTEM", 85),
            ("KYC_OCR", "OCR_EXTRACT", "SUCCESS", "PAN & Aadhaar format verified (Confidence 92%)", "APP-2026-104928", 235),
            ("BIOMETRICS", "FACE_MATCH", "SUCCESS", "Cosine similarity 0.892 (Webcam vs Aadhaar)", "APP-2026-104928", 312),
            ("CIBIL", "BUREAU_PULL", "SUCCESS", "CIBIL Score 810 retrieved, DTI 0.22", "APP-2026-104928", 182),
            ("DECISION_AI", "XAI_SANCTION", "SUCCESS", "Loan APPROVED: ₹5,00,000 (SHAP +0.38 CIBIL)", "APP-2026-104928", 118),
            ("BLOCKCHAIN", "BLOCK_MINTED", "SUCCESS", "Block #1 notarized: H_1 = SHA256(H_0...)", "APP-2026-104928", 94)
        ]
        for stage, ev_type, status, details, app_id, dur in sample_events:
            self._add_event(stage, ev_type, status, details, app_id, dur, broadcast=False)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Send initial state snapshot immediately
        snapshot = self.get_telemetry_snapshot()
        await websocket.send_json({
            "type": "SNAPSHOT",
            "data": snapshot
        })

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for dead in disconnected:
            if dead in self.active_connections:
                self.active_connections.remove(dead)

    def _add_event(self, stage: str, event_type: str, status: str, details: str, 
                   applicant_id: str, duration_ms: int, broadcast: bool = True, is_anomaly: bool = False):
        event = {
            "id": f"EVT-{len(self.events_buffer) + 1:04d}",
            "timestamp": datetime.utcnow().strftime("%H:%M:%S.%f")[:-3],
            "iso_time": datetime.utcnow().isoformat(),
            "stage": stage,
            "event_type": event_type,
            "status": status,
            "details": details,
            "applicant_id": applicant_id,
            "duration_ms": duration_ms,
            "is_anomaly": is_anomaly
        }
        
        self.events_buffer.insert(0, event)
        if len(self.events_buffer) > self.max_buffer_size:
            self.events_buffer.pop()

        self.metrics["total_requests"] += 1
        if status == "SUCCESS":
            self.metrics["successful_verifications"] += 1
        elif status in ["FAILED", "REJECTED"]:
            self.metrics["failed_verifications"] += 1
        elif status in ["HOLD", "REVIEW", "MISMATCH"]:
            self.metrics["manual_reviews"] += 1

        if is_anomaly:
            self.metrics["fraud_alerts_count"] += 1
            alert = {
                "id": f"ALT-{len(self.fraud_alerts) + 1:03d}",
                "timestamp": event["timestamp"],
                "severity": "HIGH" if status == "MISMATCH" else "MEDIUM",
                "stage": stage,
                "message": f"Anomaly on {applicant_id}: {details}"
            }
            self.fraud_alerts.insert(0, alert)
            if len(self.fraud_alerts) > 20:
                self.fraud_alerts.pop()

        return event

    def record_event(self, stage: str, event_type: str, status: str, details: str, 
                     applicant_id: str = "N/A", duration_ms: int = 100, is_anomaly: bool = False):
        event = self._add_event(stage, event_type, status, details, applicant_id, duration_ms, is_anomaly=is_anomaly)
        
        # Schedule async broadcast if event loop is running
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running() and self.active_connections:
                asyncio.create_task(self.broadcast({
                    "type": "NEW_EVENT",
                    "event": event,
                    "metrics": self.get_telemetry_snapshot()["metrics"]
                }))
        except Exception:
            pass
        return event

    def get_telemetry_snapshot(self) -> Dict[str, Any]:
        uptime_sec = int(time.time() - self.start_time)
        hours, rem = divmod(uptime_sec, 3600)
        minutes, seconds = divmod(rem, 60)
        uptime_str = f"{hours:02d}h {minutes:02d}m {seconds:02d}s"

        total = max(1, self.metrics["total_requests"])
        success_rate = round((self.metrics["successful_verifications"] / total) * 100, 1)

        # Micro-fluctuations for live feel
        simulated_cpu = round(random.uniform(12.5, 28.4), 1)
        simulated_ram = round(165.0 + random.uniform(2.0, 15.0), 1)

        return {
            "system_status": "ONLINE",
            "uptime_seconds": uptime_sec,
            "uptime_formatted": uptime_str,
            "cpu_utilization_pct": simulated_cpu,
            "memory_usage_mb": simulated_ram,
            "active_websocket_clients": len(self.active_connections),
            "metrics": {
                **self.metrics,
                "success_rate_pct": success_rate,
                "req_per_min": round(random.uniform(4.2, 12.8), 1)
            },
            "service_health": {
                "fastapi_core": {"status": "HEALTHY", "latency_ms": 12},
                "ocr_service": {"status": "HEALTHY", "latency_ms": self.metrics["stage_latencies"]["ocr"]},
                "face_biometrics": {"status": "HEALTHY", "latency_ms": self.metrics["stage_latencies"]["face_kyc"]},
                "cibil_bureau": {"status": "HEALTHY", "latency_ms": self.metrics["stage_latencies"]["cibil"]},
                "ml_risk_engine": {"status": "HEALTHY", "latency_ms": self.metrics["stage_latencies"]["ml_risk"]},
                "blockchain_node": {"status": "HEALTHY", "latency_ms": self.metrics["stage_latencies"]["blockchain"]},
                "sqlite_database": {"status": "HEALTHY", "latency_ms": 6}
            },
            "recent_events": self.events_buffer[:35],
            "fraud_alerts": self.fraud_alerts[:10]
        }

    async def trigger_simulated_pipeline(self):
        """Simulates an entire live loan application workflow across all 7 gates with real-time events"""
        names = ["Vikram Malhotra", "Ananya Sen", "Rohit Verma", "Neha Joshi", "Arjun Reddy"]
        selected_name = random.choice(names)
        app_id = f"APP-2026-{random.randint(110000, 999000)}"
        
        stages = [
            ("REGISTRATION", "USER_SIGNUP", "SUCCESS", f"New applicant registered: {selected_name}", 45),
            ("KYC_OCR", "DOC_INGEST", "SUCCESS", f"Aadhaar & PAN text extracted for {selected_name}", 245),
            ("BIOMETRICS", "FACE_DESCRIPTOR", "SUCCESS", f"WebRTC frame matched with doc photo (sim: 0.91)", 310),
            ("SECURITY_OTP", "TOTP_VERIFY", "SUCCESS", "RFC 6238 6-digit OTP validated in 38s", 32),
            ("CIBIL", "BUREAU_SYNC", "SUCCESS", f"CIBIL score {random.randint(720, 830)} verified (Prime)", 175),
            ("ML_ENGINE", "XAI_PREDICTION", "SUCCESS", "Gradient Boosting Risk: Low (SHAP explanation rendered)", 115),
            ("BLOCKCHAIN", "BLOCK_MINED", "SUCCESS", f"Minted Block #{len(self.events_buffer)+1} for {app_id}", 88)
        ]

        for stage, ev_type, status, details, dur in stages:
            self.record_event(stage, ev_type, status, details, app_id, dur)
            await asyncio.sleep(0.45) # realistic interval between stages

        return {"status": "Simulation Complete", "applicant_id": app_id, "name": selected_name}

# Global singleton
monitoring_service = MonitoringService()
