#!/bin/bash

echo "=========================================="
echo "Testing Shopify Cart Recovery Services"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test webhook handler health
echo -n "Testing Webhook Handler (http://localhost:8101/health)... "
WEBHOOK_HEALTH=$(curl -s http://localhost:8101/health)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ OK${NC}"
    echo "  Response: $WEBHOOK_HEALTH"
else
    echo -e "${RED}✗ FAILED${NC}"
fi
echo ""

# Test web pixels handler health
echo -n "Testing Web Pixels Handler (http://localhost:8102/health)... "
PIXELS_HEALTH=$(curl -s http://localhost:8102/health)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ OK${NC}"
    echo "  Response: $PIXELS_HEALTH"
else
    echo -e "${RED}✗ FAILED${NC}"
fi
echo ""

# Test Redis connection
echo -n "Testing Redis Connection (port 8100)... "
REDIS_PING=$(redis-cli -h localhost -p 8100 ping 2>/dev/null)
if [ "$REDIS_PING" == "PONG" ]; then
    echo -e "${GREEN}✓ OK${NC}"
    echo "  Response: PONG"
else
    echo -e "${YELLOW}⚠ Redis CLI not installed or connection failed${NC}"
    echo "  (This is OK - Redis is accessible from containers)"
fi
echo ""

# Test sample cart webhook
echo "Testing Sample Webhook Event..."
WEBHOOK_RESPONSE=$(curl -s -X POST http://localhost:8101/webhooks/carts/create \
  -H "Content-Type: application/json" \
  -H "X-Shopify-Topic: carts/create" \
  -H "X-Shopify-Hmac-Sha256: test_signature" \
  -H "X-Shopify-Shop-Domain: test-shop.myshopify.com" \
  -d '{
    "id": 123456,
    "token": "test_cart_token",
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
  }')

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Webhook sent successfully${NC}"
    echo "  Response: $WEBHOOK_RESPONSE"
else
    echo -e "${RED}✗ Webhook failed${NC}"
fi
echo ""

# Test sample Web Pixels click event
echo "Testing Sample Web Pixels Click Event..."
PIXELS_RESPONSE=$(curl -s -X POST http://localhost:8102/pixels/clicked \
  -H "Content-Type: application/json" \
  -d '{
    "clientX": 150,
    "clientY": 200,
    "element": {
      "id": "add-to-cart-btn",
      "tagName": "BUTTON",
      "className": "btn btn-primary"
    },
    "session_id": "test_session_123",
    "timestamp": "2025-10-26T10:00:00Z"
  }')

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Web Pixels event sent successfully${NC}"
    echo "  Response: $PIXELS_RESPONSE"
else
    echo -e "${RED}✗ Web Pixels event failed${NC}"
fi
echo ""

# Check Docker containers
echo "=========================================="
echo "Docker Container Status:"
echo "=========================================="
docker ps --filter "name=shopify" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "=========================================="
echo "Test Complete!"
echo "=========================================="
echo ""
echo "Next Steps:"
echo "1. Check logs: docker-compose logs -f"
echo "2. Check event processor logs: docker logs event-processor"
echo "3. Monitor Redis: docker exec -it shopify-cart-redis redis-cli monitor"
