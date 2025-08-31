import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.redis_client import get_redis_client
from shared.logging_config import get_logger
from shared.config import get_settings
from .models import EventProcessor

logger = get_logger("shopify_webhook_handler")
settings = get_settings()

app = FastAPI(title="Shopify Webhook Handler", version="1.0.0")

redis_client = None
event_processor = EventProcessor()

MAX_PAYLOAD_SIZE = 1024 * 1024  # 1MB
WEBHOOK_TIMEOUT = 300  # 5 minutes


class WebhookRateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    def is_allowed(self, shop_domain: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        
        if shop_domain not in self.requests:
            self.requests[shop_domain] = []
        
        self.requests[shop_domain] = [
            req_time for req_time in self.requests[shop_domain] 
            if req_time > window_start
        ]
        
        if len(self.requests[shop_domain]) >= self.max_requests:
            return False
        
        self.requests[shop_domain].append(now)
        return True


rate_limiter = WebhookRateLimiter()


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    if not signature or not secret:
        return False
    
    try:
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        received_signature = signature.replace('sha256=', '')
        return hmac.compare_digest(expected_signature, received_signature)
    
    except Exception as e:
        logger.error(f"HMAC verification error: {e}")
        return False


def verify_timestamp(timestamp_header: Optional[str]) -> bool:
    if not timestamp_header:
        return False
    
    try:
        webhook_timestamp = int(timestamp_header)
        current_timestamp = int(time.time())
        
        if abs(current_timestamp - webhook_timestamp) > WEBHOOK_TIMEOUT:
            return False
        
        return True
    
    except (ValueError, TypeError):
        return False


async def validate_webhook_request(
    request: Request,
    x_shopify_hmac_sha256: Optional[str] = Header(None),
    x_shopify_timestamp: Optional[str] = Header(None),
    x_shopify_shop_domain: Optional[str] = Header(None),
    x_shopify_topic: Optional[str] = Header(None)
):
    if not x_shopify_shop_domain:
        raise HTTPException(status_code=400, detail="Missing shop domain header")
    
    if not x_shopify_topic:
        raise HTTPException(status_code=400, detail="Missing webhook topic header")
    
    if not rate_limiter.is_allowed(x_shopify_shop_domain):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for shop")
    
    payload = await request.body()
    
    if len(payload) > MAX_PAYLOAD_SIZE:
        raise HTTPException(status_code=413, detail="Payload too large")
    
    if not verify_webhook_signature(payload, x_shopify_hmac_sha256, settings.shopify.webhook_secret):
        logger.warning(f"Invalid HMAC signature from {x_shopify_shop_domain}")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    if not verify_timestamp(x_shopify_timestamp):
        logger.warning(f"Invalid timestamp from {x_shopify_shop_domain}")
        raise HTTPException(status_code=401, detail="Invalid or expired timestamp")
    
    try:
        payload_data = json.loads(payload.decode('utf-8'))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    return {
        "payload": payload_data,
        "shop_domain": x_shopify_shop_domain,
        "topic": x_shopify_topic,
        "timestamp": x_shopify_timestamp
    }


async def process_webhook(webhook_data: Dict[str, Any]):
    try:
        redis_event = event_processor.process_webhook(
            webhook_data["topic"],
            webhook_data["payload"],
            webhook_data["shop_domain"]
        )
        
        channel_map = {
            "carts/create": "cart_events",
            "carts/update": "cart_events",
            "checkouts/create": "checkout_events",
            "checkouts/update": "checkout_events",
            "customers/create": "customer_events",
            "customers/update": "customer_events",
            "orders/create": "order_events",
            "orders/paid": "order_events",
            "orders/fulfilled": "order_events"
        }
        
        channel = channel_map.get(webhook_data["topic"], "webhook_events")
        success = await redis_client.publish_event(channel, redis_event)
        
        logger.info(f"Processed webhook: {webhook_data['topic']}", {
            "topic": webhook_data["topic"],
            "shop_domain": webhook_data["shop_domain"],
            "event_id": redis_event["event_id"],
            "customer_id": redis_event.get("customer_id"),
            "redis_published": success
        })
        
        return {"status": "success", "event_id": redis_event["event_id"]}
    
    except ValidationError as e:
        logger.error(f"Validation error for {webhook_data['topic']}: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid webhook data: {e}")
    except Exception as e:
        logger.error(f"Error processing webhook {webhook_data['topic']}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.on_event("startup")
async def startup_event():
    global redis_client
    redis_client = await get_redis_client()
    logger.info("Shopify Webhook Handler started")


@app.on_event("shutdown")
async def shutdown_event():
    from shared.redis_client import close_redis_client
    await close_redis_client()
    logger.info("Shopify Webhook Handler stopped")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info("Webhook request processed", {
        "method": request.method,
        "url": str(request.url),
        "status_code": response.status_code,
        "process_time_ms": process_time * 1000,
        "shop_domain": request.headers.get("x-shopify-shop-domain"),
        "topic": request.headers.get("x-shopify-topic")
    })
    
    return response


@app.post("/webhooks/carts/create")
async def handle_cart_create(webhook_data: Dict[str, Any] = Depends(validate_webhook_request)):
    return await process_webhook(webhook_data)


@app.post("/webhooks/carts/update")
async def handle_cart_update(webhook_data: Dict[str, Any] = Depends(validate_webhook_request)):
    return await process_webhook(webhook_data)


@app.post("/webhooks/checkouts/create")
async def handle_checkout_create(webhook_data: Dict[str, Any] = Depends(validate_webhook_request)):
    return await process_webhook(webhook_data)


@app.post("/webhooks/checkouts/update")
async def handle_checkout_update(webhook_data: Dict[str, Any] = Depends(validate_webhook_request)):
    return await process_webhook(webhook_data)


@app.post("/webhooks/customers/create")
async def handle_customer_create(webhook_data: Dict[str, Any] = Depends(validate_webhook_request)):
    return await process_webhook(webhook_data)


@app.post("/webhooks/customers/update")
async def handle_customer_update(webhook_data: Dict[str, Any] = Depends(validate_webhook_request)):
    return await process_webhook(webhook_data)


@app.post("/webhooks/orders/create")
async def handle_order_create(webhook_data: Dict[str, Any] = Depends(validate_webhook_request)):
    return await process_webhook(webhook_data)


@app.post("/webhooks/orders/paid")
async def handle_order_paid(webhook_data: Dict[str, Any] = Depends(validate_webhook_request)):
    return await process_webhook(webhook_data)


@app.post("/webhooks/orders/fulfilled")
async def handle_order_fulfilled(webhook_data: Dict[str, Any] = Depends(validate_webhook_request)):
    return await process_webhook(webhook_data)


@app.get("/health")
async def health_check():
    redis_healthy = await redis_client.health_check() if redis_client else False
    
    return {
        "status": "healthy" if redis_healthy else "unhealthy",
        "redis_connection": redis_healthy,
        "webhook_secret_configured": bool(settings.shopify.webhook_secret),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/metrics")
async def get_metrics():
    return {
        "rate_limiting": {
            "active_shops": len(rate_limiter.requests),
            "max_requests_per_minute": rate_limiter.max_requests
        },
        "configuration": {
            "max_payload_size_mb": MAX_PAYLOAD_SIZE / (1024 * 1024),
            "webhook_timeout_seconds": WEBHOOK_TIMEOUT
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.app.host, port=settings.app.port)