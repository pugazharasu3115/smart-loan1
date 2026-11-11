from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any
from backend.services.monitoring_service import monitoring_service

router = APIRouter(prefix="/api/monitoring", tags=["Real-Time Monitoring"])

@router.get("/metrics")
def get_system_metrics() -> Dict[str, Any]:
    """Retrieve full system health, stage latencies, uptime, and fraud alerts snapshot"""
    return monitoring_service.get_telemetry_snapshot()

@router.get("/events")
def get_recent_events(limit: int = 50):
    """Retrieve list of recent system telemetry events"""
    return monitoring_service.events_buffer[:limit]

@router.post("/simulate-traffic")
async def trigger_simulated_traffic():
    """Trigger an interactive real-time multi-gate verification pipeline simulation"""
    res = await monitoring_service.trigger_simulated_pipeline()
    return {"success": True, "details": res}

@router.post("/clear-logs")
def clear_monitoring_logs():
    """Reset event stream logs buffer"""
    monitoring_service.events_buffer = []
    monitoring_service.metrics["total_requests"] = 0
    monitoring_service.metrics["successful_verifications"] = 0
    monitoring_service.metrics["failed_verifications"] = 0
    monitoring_service.metrics["manual_reviews"] = 0
    return {"success": True, "message": "Monitoring logs cleared"}

# WebSocket endpoint on router or root
@router.websocket("/stream")
async def websocket_monitoring_stream(websocket: WebSocket):
    """Real-time bi-directional streaming WebSocket connection for live telemetry updates"""
    await monitoring_service.connect(websocket)
    try:
        while True:
            # Keep socket alive and allow client to request ping/action
            data = await websocket.receive_text()
            if data == "PING":
                await websocket.send_json({"type": "PONG", "timestamp": monitoring_service.get_telemetry_snapshot()["uptime_formatted"]})
            elif data == "SIMULATE":
                await monitoring_service.trigger_simulated_pipeline()
    except WebSocketDisconnect:
        monitoring_service.disconnect(websocket)
    except Exception:
        monitoring_service.disconnect(websocket)
