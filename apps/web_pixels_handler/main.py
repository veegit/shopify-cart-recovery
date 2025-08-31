import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from uuid import uuid4
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.redis_client import get_redis_client
from shared.logging_config import get_logger
from shared.config import get_settings
from .models import (
    ClickedEventModel, InputChangedEventModel, InputFocusedEventModel,
    InputBlurredEventModel, FormSubmittedEventModel, PageViewedEventModel,
    WebPixelEventProcessor
)

logger = get_logger("web_pixels_handler")
settings = get_settings()

app = FastAPI(title="Web Pixels Handler", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

redis_client = None
event_processor = WebPixelEventProcessor()
session_store = {}
performance_metrics = {
    "total_events": 0,
    "events_per_second": 0,
    "last_minute_events": [],
    "avg_processing_time": 0,
    "processing_times": []
}


class RateLimiter:
    def __init__(self, max_requests: int = 1000, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id] 
            if req_time > window_start
        ]
        
        if len(self.requests[client_id]) >= self.max_requests:
            return False
        
        self.requests[client_id].append(now)
        return True


rate_limiter = RateLimiter()


def get_client_id(request: Request) -> str:
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_or_create_session(request: Request, customer_id: Optional[str] = None) -> Dict[str, Any]:
    session_id = request.headers.get("x-session-id")
    
    if not session_id:
        session_id = str(uuid4())
    
    if session_id not in session_store:
        session_store[session_id] = {
            "session_id": session_id,
            "customer_id": customer_id,
            "shop_domain": request.headers.get("x-shop-domain"),
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "event_count": 0
        }
    
    session_store[session_id]["last_activity"] = datetime.utcnow()
    session_store[session_id]["event_count"] += 1
    
    if customer_id and not session_store[session_id]["customer_id"]:
        session_store[session_id]["customer_id"] = customer_id
    
    return session_store[session_id]


def cleanup_expired_sessions():
    cutoff_time = datetime.utcnow() - timedelta(hours=2)
    expired_sessions = [
        sid for sid, session in session_store.items()
        if session["last_activity"] < cutoff_time
    ]
    
    for sid in expired_sessions:
        del session_store[sid]
    
    if expired_sessions:
        logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")


def update_performance_metrics(processing_time: float):
    now = time.time()
    performance_metrics["total_events"] += 1
    performance_metrics["last_minute_events"].append(now)
    performance_metrics["processing_times"].append(processing_time)
    
    performance_metrics["last_minute_events"] = [
        t for t in performance_metrics["last_minute_events"] 
        if now - t <= 60
    ]
    
    performance_metrics["events_per_second"] = len(performance_metrics["last_minute_events"]) / 60
    
    if len(performance_metrics["processing_times"]) > 1000:
        performance_metrics["processing_times"] = performance_metrics["processing_times"][-1000:]
    
    if performance_metrics["processing_times"]:
        performance_metrics["avg_processing_time"] = sum(performance_metrics["processing_times"]) / len(performance_metrics["processing_times"])


async def process_web_pixel_event(
    event_type: str,
    payload: Dict[str, Any],
    request: Request,
    customer_id: Optional[str] = None
):
    start_time = time.time()
    client_id = get_client_id(request)
    
    if not rate_limiter.is_allowed(client_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    try:
        session_context = get_or_create_session(request, customer_id)
        redis_event = event_processor.process_event(event_type, payload, session_context)
        
        channel_map = {
            "clicked": "click_events",
            "input_changed": "dom_events", 
            "input_focused": "dom_events",
            "input_blurred": "dom_events",
            "form_submitted": "form_events",
            "page_viewed": "dom_events"
        }
        
        channel = channel_map.get(event_type, "dom_events")
        success = await redis_client.publish_event(channel, redis_event)
        
        processing_time = time.time() - start_time
        update_performance_metrics(processing_time)
        
        logger.info(f"Processed {event_type} event", {
            "event_type": event_type,
            "session_id": session_context["session_id"],
            "customer_id": session_context.get("customer_id"),
            "processing_time_ms": processing_time * 1000,
            "redis_published": success,
            "client_id": client_id
        })
        
        return {
            "status": "success",
            "event_id": redis_event["event_id"],
            "session_id": session_context["session_id"]
        }
    
    except ValidationError as e:
        logger.error(f"Validation error for {event_type}: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid event data: {e}")
    except Exception as e:
        logger.error(f"Error processing {event_type}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.on_event("startup")
async def startup_event():
    global redis_client
    redis_client = await get_redis_client()
    logger.info("Web Pixels Handler started")


@app.on_event("shutdown")
async def shutdown_event():
    from shared.redis_client import close_redis_client
    await close_redis_client()
    logger.info("Web Pixels Handler stopped")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info("Request processed", {
        "method": request.method,
        "url": str(request.url),
        "status_code": response.status_code,
        "process_time_ms": process_time * 1000,
        "client_id": get_client_id(request)
    })
    
    return response


@app.post("/pixels/clicked")
async def handle_clicked_event(
    request: Request,
    payload: Dict[str, Any],
    x_customer_id: Optional[str] = Header(None)
):
    return await process_web_pixel_event("clicked", payload, request, x_customer_id)


@app.post("/pixels/input_changed")
async def handle_input_changed_event(
    request: Request,
    payload: Dict[str, Any],
    x_customer_id: Optional[str] = Header(None)
):
    return await process_web_pixel_event("input_changed", payload, request, x_customer_id)


@app.post("/pixels/input_focused")
async def handle_input_focused_event(
    request: Request,
    payload: Dict[str, Any],
    x_customer_id: Optional[str] = Header(None)
):
    return await process_web_pixel_event("input_focused", payload, request, x_customer_id)


@app.post("/pixels/input_blurred")
async def handle_input_blurred_event(
    request: Request,
    payload: Dict[str, Any],
    x_customer_id: Optional[str] = Header(None)
):
    return await process_web_pixel_event("input_blurred", payload, request, x_customer_id)


@app.post("/pixels/form_submitted")
async def handle_form_submitted_event(
    request: Request,
    payload: Dict[str, Any],
    x_customer_id: Optional[str] = Header(None)
):
    return await process_web_pixel_event("form_submitted", payload, request, x_customer_id)


@app.post("/pixels/page_viewed")
async def handle_page_viewed_event(
    request: Request,
    payload: Dict[str, Any],
    x_customer_id: Optional[str] = Header(None)
):
    return await process_web_pixel_event("page_viewed", payload, request, x_customer_id)


@app.get("/health")
async def health_check():
    redis_healthy = await redis_client.health_check() if redis_client else False
    
    cleanup_expired_sessions()
    
    return {
        "status": "healthy" if redis_healthy else "unhealthy",
        "redis_connection": redis_healthy,
        "active_sessions": len(session_store),
        "performance_metrics": {
            "total_events": performance_metrics["total_events"],
            "events_per_second": round(performance_metrics["events_per_second"], 2),
            "avg_processing_time_ms": round(performance_metrics["avg_processing_time"] * 1000, 2)
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/metrics")
async def get_metrics():
    return {
        "sessions": {
            "active_count": len(session_store),
            "total_events": sum(s["event_count"] for s in session_store.values())
        },
        "performance": performance_metrics,
        "rate_limiting": {
            "active_clients": len(rate_limiter.requests)
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.app.host, port=settings.app.port)