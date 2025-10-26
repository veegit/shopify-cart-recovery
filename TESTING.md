# Local Testing Guide

## ⚙️ Development vs Production Mode

**Development Mode (Default for Local Testing):**
- Webhook signature validation is **disabled** for easier testing
- No need to generate valid HMAC signatures
- Set with `APP_ENV=development` in `.env` file
- **⚠️ NEVER use in production!**

**Production Mode:**
- Webhook signature validation is **enabled** and strictly enforced
- Requires valid HMAC-SHA256 signatures from Shopify
- Set with `APP_ENV=production` in `.env` file
- Use `generate_webhook_signature.py` to create test requests

The project is configured for **development mode** by default, making local testing simple and straightforward.

---

## Quick Start

### 1. Start All Services with Docker

```bash
# Make sure you're in the project directory
cd /home/user/shopify-cart-recovery

# Start all services
docker-compose up --build

# Or run in background (detached mode)
docker-compose up -d --build
```

**Wait for all services to start** (about 30-60 seconds). You should see:
- `shopify-cart-redis` on port 8100
- `shopify-webhook-handler` on port 8101
- `web-pixels-handler` on port 8102
- `event-processor` processing events

### 2. Run Quick Tests

```bash
# Python test suite (recommended)
python3 test_services.py

# Or bash test script
./test_local.sh
```

---

## Testing Each Component

### Test 1: Health Checks

```bash
# Webhook handler
curl http://localhost:8101/health

# Web Pixels handler
curl http://localhost:8102/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "webhook-handler",
  "redis": "connected"
}
```

### Test 2: Send a Webhook Event

**Development Mode (No Signature Required):**

When `APP_ENV=development` in your `.env` file, signature validation is disabled for easier testing:

```bash
curl -X POST http://localhost:8101/webhooks/carts/create \
  -H "Content-Type: application/json" \
  -H "X-Shopify-Topic: carts/create" \
  -H "X-Shopify-Hmac-Sha256: dev_mode_signature_not_validated" \
  -H "X-Shopify-Shop-Domain: test-shop.myshopify.com" \
  -d '{
    "id": 123456,
    "token": "cart_abc123",
    "line_items": [
      {
        "id": 1,
        "product_id": 789,
        "quantity": 2,
        "price": "29.99"
      }
    ],
    "created_at": "2025-10-26T10:00:00Z",
    "updated_at": "2025-10-26T10:00:00Z"
  }'
```

**Expected Response (Development Mode):**
```json
{
  "status": "success",
  "event_id": "uuid-here"
}
```

**Production Mode (Valid Signature Required):**

For production testing with signature validation, use the signature generator:

```bash
# Generate a valid signed request
python3 generate_webhook_signature.py your_webhook_secret
```

### Test 3: Send a Web Pixels Click Event

```bash
curl -X POST http://localhost:8102/pixels/clicked \
  -H "Content-Type: application/json" \
  -d '{
    "clientX": 150,
    "clientY": 200,
    "element": {
      "id": "add-to-cart-btn",
      "tagName": "BUTTON",
      "className": "btn-primary"
    },
    "session_id": "session_123",
    "timestamp": "2025-10-26T10:00:00Z"
  }'
```

### Test 4: Send a Form Input Event

```bash
curl -X POST http://localhost:8102/pixels/input_changed \
  -H "Content-Type: application/json" \
  -d '{
    "element": {
      "id": "email",
      "tagName": "INPUT",
      "value": "test@example.com"
    },
    "session_id": "session_123",
    "timestamp": "2025-10-26T10:00:00Z"
  }'
```

---

## Monitoring and Debugging

### View Live Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker logs -f event-processor
docker logs -f shopify-webhook-handler
docker logs -f web-pixels-handler
```

### Monitor Redis Events

```bash
# Watch all Redis commands
docker exec -it shopify-cart-redis redis-cli MONITOR

# Subscribe to specific channel
docker exec -it shopify-cart-redis redis-cli
> SUBSCRIBE cart_events
> SUBSCRIBE dom_events
```

### Check Container Status

```bash
# List running containers
docker-compose ps

# Check container health
docker ps --filter "name=shopify"
```

### Access Container Shell

```bash
# Webhook handler container
docker exec -it shopify-webhook-handler /bin/bash

# Redis container
docker exec -it shopify-cart-redis redis-cli
```

---

## Running Unit Tests

```bash
# Run all tests
docker-compose run --rm shopify-webhooks pytest

# Run specific test file
docker-compose run --rm shopify-webhooks pytest tests/test_webhook_handler.py

# Run with verbose output
docker-compose run --rm shopify-webhooks pytest -v

# Run with coverage
docker-compose run --rm shopify-webhooks pytest --cov=apps
```

---

## Common Issues and Solutions

### Issue: Containers won't start

```bash
# Check for port conflicts
lsof -i :8100 -i :8101 -i :8102

# Stop and remove old containers
docker-compose down -v

# Rebuild from scratch
docker-compose up --build --force-recreate
```

### Issue: Redis connection refused

```bash
# Check Redis is running
docker ps | grep redis

# Test Redis connection
docker exec shopify-cart-redis redis-cli ping

# View Redis logs
docker logs shopify-cart-redis
```

### Issue: Events not being processed

```bash
# Check event processor logs
docker logs event-processor

# Verify Redis channels
docker exec -it shopify-cart-redis redis-cli
> PUBSUB CHANNELS
> PUBSUB NUMSUB cart_events dom_events
```

### Issue: Permission denied on test scripts

```bash
chmod +x test_local.sh test_services.py
```

---

## Service Endpoints

| Service | Port | Endpoints |
|---------|------|-----------|
| **Webhook Handler** | 8101 | `/health`<br>`/webhooks/carts/create`<br>`/webhooks/carts/update`<br>`/webhooks/checkouts/create`<br>`/webhooks/orders/create` |
| **Web Pixels Handler** | 8102 | `/health`<br>`/pixels/clicked`<br>`/pixels/input_changed`<br>`/pixels/input_focused`<br>`/pixels/form_submitted`<br>`/pixels/page_viewed` |
| **Redis** | 8100 | Redis protocol (6379 internal) |
| **Event Processor** | - | Background service (no HTTP endpoint) |

---

## What to Look For

### Success Indicators

1. **All containers running**
   ```bash
   docker-compose ps
   # All services should show "Up" status
   ```

2. **Health checks passing**
   ```bash
   curl http://localhost:8101/health
   curl http://localhost:8102/health
   # Both should return 200 OK
   ```

3. **Events being processed**
   ```bash
   docker logs event-processor
   # Should show "Received event" messages
   ```

4. **Redis channels active**
   ```bash
   docker exec -it shopify-cart-redis redis-cli PUBSUB CHANNELS
   # Should list: cart_events, dom_events, etc.
   ```

### Log Examples

**Successful webhook processing:**
```
INFO - Received cart/create webhook
INFO - Publishing event to cart_events channel
INFO - Event published successfully
```

**Successful Web Pixels event:**
```
INFO - Received click event at (150, 200)
INFO - Session: session_123
INFO - Publishing to dom_events channel
```

**Event processor receiving events:**
```
INFO - Subscribed to channels: cart_events, dom_events, checkout_events
INFO - Received event from cart_events
INFO - Processing cart creation event
```

---

## Production Checklist

Before deploying to production:

- [ ] Update `.env` with real Shopify credentials
- [ ] Set `APP_ENV=production`
- [ ] Configure proper HMAC webhook verification
- [ ] Set up HTTPS/SSL certificates
- [ ] Configure CORS for your actual domain
- [ ] Set up monitoring and alerting
- [ ] Configure proper logging (log aggregation)
- [ ] Set resource limits in docker-compose.yml
- [ ] Enable Redis persistence
- [ ] Set up backup and disaster recovery

---

## Next Steps

1. **Test the full flow**: Send events and watch them flow through the system
2. **Integrate with Shopify**: Set up webhooks in Shopify admin
3. **Install Web Pixels**: Deploy the pixel.js to your Shopify store
4. **Monitor performance**: Watch logs and Redis activity
5. **Add ML logic**: Implement cart recovery predictions (MVP Part 2)
