# Shopify Cart Recovery - Dual-Stream Analytics Platform

A comprehensive cart recovery solution that combines traditional Shopify webhooks with advanced Web Pixels DOM event tracking for unprecedented visibility into customer behavior patterns and cart abandonment signals.

## 🏗️ Architecture Overview

This application implements a **dual-stream data architecture** that captures both server-side business events and client-side user interactions:

### Data Streams

1. **Shopify Webhooks** (Server-to-Server)
   - Cart creation/updates
   - Checkout events
   - Order completion
   - Customer data changes
   - Real-time business event notifications

2. **Web Pixels DOM Events** (Client-Side)
   - Mouse clicks and coordinates
   - Form interactions and submissions
   - Page engagement metrics
   - Scroll behavior and time on page
   - Fine-grained user behavior tracking

### Multi-Service Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Shopify       │    │   Web Browser    │    │   Redis PubSub  │
│   Webhooks      │───▶│   Web Pixels     │───▶│   Multi-Channel │
│   (Port 8001)   │    │   (JavaScript)   │    │   Event Stream  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
                                               ┌─────────────────┐
                                               │ Event Processor │
                                               │ Behavioral      │
                                               │ Analytics       │
                                               └─────────────────┘
```

### Business Value

- **Enhanced Cart Recovery**: Identify abandonment signals before customers leave
- **Behavioral Insights**: Understand user hesitation patterns and friction points
- **Session Correlation**: Link DOM interactions to business outcomes
- **Advanced Analytics**: Mouse movement patterns, form abandonment detection
- **Real-time Processing**: Sub-second event processing and pattern recognition

## 🚀 Quick Start Guide

### Prerequisites

- Docker and Docker Compose
- Node.js 16+ (for local development)
- Shopify Partner Account
- Redis (included in Docker setup)

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd shopify-cart-recovery

# Copy environment template
cp .env.example .env

# Update .env with your Shopify credentials
SHOPIFY_API_KEY=your_api_key
SHOPIFY_API_SECRET=your_api_secret
SHOPIFY_WEBHOOK_SECRET=your_webhook_secret
SHOPIFY_APP_URL=https://your-domain.com
WEB_PIXELS_ENDPOINT=https://your-domain.com/pixels
```

### 2. Docker Development Setup

```bash
# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps

# View logs
docker-compose logs -f shopify-webhooks
docker-compose logs -f web-pixels-handler
docker-compose logs -f event-processor
```

### 3. Service Endpoints

- **Webhook Handler**: http://localhost:8001
- **Web Pixels Handler**: http://localhost:8002
- **Redis**: localhost:6379
- **Health Checks**: 
  - http://localhost:8001/health
  - http://localhost:8002/health

### 4. Individual Service Management

```bash
# Run specific services
python main.py webhook-handler      # Shopify webhooks only
python main.py web-pixels-handler   # DOM events only
python main.py event-processor      # Event processing only
python main.py all                  # All services

# Health check
python main.py health
```

## 📡 API Endpoints

### Shopify Webhook Endpoints (Port 8001)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/webhooks/carts/create` | POST | New cart creation |
| `/webhooks/carts/update` | POST | Cart modifications |
| `/webhooks/checkouts/create` | POST | Checkout initiation |
| `/webhooks/checkouts/update` | POST | Checkout modifications |
| `/webhooks/orders/create` | POST | Order completion |
| `/webhooks/orders/paid` | POST | Payment confirmation |
| `/webhooks/customers/create` | POST | New customer registration |
| `/health` | GET | Service health check |
| `/metrics` | GET | Performance metrics |

### Web Pixels DOM Event Endpoints (Port 8002)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/pixels/clicked` | POST | Mouse click events |
| `/pixels/input_changed` | POST | Form input modifications |
| `/pixels/input_focused` | POST | Form field focus events |
| `/pixels/input_blurred` | POST | Form field blur events |
| `/pixels/form_submitted` | POST | Form submission events |
| `/pixels/page_viewed` | POST | Page view and engagement |
| `/health` | GET | Service health check |
| `/metrics` | GET | Performance and session metrics |

### Event Schemas

#### Webhook Event Schema
```json
{
  "event_id": "uuid",
  "event_type": "cart_create|checkout_create|order_create",
  "timestamp": "ISO-8601",
  "shop_domain": "store.myshopify.com",
  "customer_id": "customer_id",
  "session_id": "session_id",
  "source": "shopify_webhook",
  "data": {
    "cart_id": "cart_123",
    "total_price": "99.99",
    "currency": "USD",
    "line_items": [...]
  }
}
```

#### Web Pixels Event Schema
```json
{
  "event_id": "uuid",
  "event_type": "clicked|input_changed|form_submitted|page_viewed",
  "timestamp": "ISO-8601",
  "session_id": "session_id",
  "customer_id": "customer_id",
  "shop_domain": "store.myshopify.com",
  "source": "web_pixels",
  "data": {
    "clientX": 150,
    "clientY": 250,
    "element_tag": "button",
    "element_id": "add-to-cart",
    "url": "https://store.com/products/item"
  }
}
```

## 🎯 Web Pixels Installation

### Step 1: Create Web Pixel in Shopify Admin

1. Navigate to **Settings > Customer events**
2. Click **Add custom pixel**
3. Enter pixel name: "Cart Recovery Analytics"
4. Paste the contents of `web_pixels/pixel.js`
5. Configure permissions and data access

### Step 2: Update Configuration

```javascript
// Update endpoint in pixel.js
const CONFIG = {
    API_BASE_URL: 'https://your-domain.com',
    // ... other config
};
```

### Step 3: Test Installation

```bash
# Monitor Web Pixels events
curl -X GET http://localhost:8002/metrics

# Check session tracking
curl -X GET http://localhost:8002/health
```

## 🔧 Development

### Local Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run individual services
uvicorn apps.shopify_webhook_handler.main:app --port 8001 --reload
uvicorn apps.web_pixels_handler.main:app --port 8002 --reload

# Run event processor
python apps/event_processor/main.py
```

### Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m performance   # Performance tests only

# Run with coverage
pytest --cov=apps --cov-report=html
```

### Redis Channel Monitoring

```bash
# Monitor all channels
redis-cli MONITOR

# Subscribe to specific channels
redis-cli SUBSCRIBE cart_events checkout_events order_events
redis-cli SUBSCRIBE click_events dom_events form_events
```

## 📊 Event Processing & Analytics

### Session Correlation

The system automatically correlates events using:

- **Session ID**: Generated client-side, persistent across page views
- **Customer ID**: Extracted from Shopify customer data
- **Timestamp Correlation**: Events linked by temporal proximity
- **Behavioral Patterns**: Mouse movements, click density, form interactions

### Abandonment Detection

Automatically detects abandonment signals:

```python
signals = {
    "rapid_clicks": False,        # > 10 clicks in short timespan
    "form_abandonment": False,    # Form started but not submitted
    "cart_without_checkout": False, # Cart created but no checkout
    "hesitation_pattern": False,  # Erratic mouse movements
    "exit_intent": False         # Patterns indicating exit intent
}
```

### Behavioral Analytics

- **Click Pattern Analysis**: Focused vs scattered clicking behavior
- **Form Engagement**: Field focus time, completion rates
- **Page Engagement**: Time on page, scroll depth
- **Session Quality**: Engagement scores, intent classification
- **Conversion Correlation**: DOM behavior linked to purchase outcomes

## 🏭 Production Deployment

### Environment Variables

```bash
# Core Application
APP_ENV=production
APP_PORT=8000

# Redis Configuration  
REDIS_HOST=your-redis-host
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password

# Shopify Integration
SHOPIFY_API_KEY=your_production_api_key
SHOPIFY_API_SECRET=your_production_api_secret
SHOPIFY_WEBHOOK_SECRET=your_webhook_secret
SHOPIFY_APP_URL=https://your-production-domain.com

# Web Pixels
WEB_PIXELS_ENDPOINT=https://your-production-domain.com/pixels

# Performance Settings
MAX_BATCH_SIZE=100
BATCH_TIMEOUT_MS=2000
MAX_RETRY_ATTEMPTS=3
```

### Docker Production Deployment

```bash
# Build production image
docker build -t shopify-cart-recovery:latest .

# Deploy with production compose
docker-compose -f docker-compose.prod.yml up -d

# Scale services
docker-compose -f docker-compose.prod.yml up -d --scale web-pixels-handler=3
```

### Load Balancer Configuration

```nginx
upstream webhook_handlers {
    server webhook-handler-1:8000;
    server webhook-handler-2:8000;
}

upstream pixels_handlers {
    server pixels-handler-1:8000;
    server pixels-handler-2:8000;
    server pixels-handler-3:8000;
}

server {
    listen 443 ssl;
    server_name your-domain.com;
    
    location /webhooks/ {
        proxy_pass http://webhook_handlers;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /pixels/ {
        proxy_pass http://pixels_handlers;
        proxy_set_header X-Real-IP $remote_addr;
        
        # CORS for browser requests
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
    }
}
```

## 📈 Monitoring & Alerting

### Health Checks

```bash
# Service health
curl https://your-domain.com/webhooks/health
curl https://your-domain.com/pixels/health

# Metrics endpoints
curl https://your-domain.com/webhooks/metrics
curl https://your-domain.com/pixels/metrics
```

### Key Metrics to Monitor

- **Event Processing Rate**: Events per second across both streams
- **Session Correlation Rate**: Successfully correlated DOM + webhook events
- **Redis Queue Depth**: Pub/sub message backlog
- **Error Rates**: Failed event processing by service
- **Response Times**: API endpoint latency
- **Abandonment Detection**: Cart abandonment signal frequency

### Alerting Thresholds

```yaml
alerts:
  - name: High Error Rate
    condition: error_rate > 5%
    duration: 5m
    
  - name: Low Event Processing
    condition: events_per_second < 10
    duration: 2m
    
  - name: Redis Connection Loss
    condition: redis_healthy == false
    duration: 30s
    
  - name: High Cart Abandonment
    condition: abandonment_rate > 70%
    duration: 10m
```

## 🔒 Security & Compliance

### Webhook Security

- **HMAC Verification**: All webhooks verified with SHA256 signatures
- **Timestamp Validation**: Rejects requests older than 5 minutes
- **Rate Limiting**: 100 requests per minute per shop
- **Payload Size Limits**: Maximum 1MB payload size

### Web Pixels Privacy

- **Consent Management**: Respects user privacy preferences
- **Data Minimization**: Only essential data collected
- **Opt-out Support**: Users can disable tracking
- **GDPR Compliance**: Privacy-first data collection

### Data Security

```bash
# Environment secrets management
export SHOPIFY_WEBHOOK_SECRET=$(vault kv get -field=secret secret/shopify)
export REDIS_PASSWORD=$(vault kv get -field=password secret/redis)

# TLS encryption for all external communication
# Internal service communication over encrypted Docker networks
# Redis AUTH enabled in production
```

## 🛠️ Troubleshooting

### Common Issues

1. **Webhook HMAC Verification Failed**
   ```bash
   # Check webhook secret configuration
   echo $SHOPIFY_WEBHOOK_SECRET
   
   # Verify webhook payload in logs
   docker-compose logs shopify-webhooks | grep "HMAC"
   ```

2. **Web Pixels Events Not Received**
   ```bash
   # Check CORS configuration
   curl -X OPTIONS http://localhost:8002/pixels/clicked
   
   # Monitor network requests in browser dev tools
   # Verify API_BASE_URL in pixel.js
   ```

3. **Redis Connection Issues**
   ```bash
   # Test Redis connectivity
   redis-cli -h localhost -p 6379 ping
   
   # Check Redis logs
   docker-compose logs redis
   ```

4. **Event Processing Delays**
   ```bash
   # Monitor event processor
   docker-compose logs event-processor
   
   # Check Redis queue depth
   redis-cli PUBSUB CHANNELS
   ```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with detailed logging
python main.py all
```

## 📚 API Documentation

Full API documentation is available at:
- Webhook Handler: http://localhost:8001/docs
- Web Pixels Handler: http://localhost:8002/docs

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`pytest`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push branch (`git push origin feature/amazing-feature`)
6. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: See `/docs` directory for detailed guides
- **Issues**: Open GitHub issues for bugs and feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas

---

**Built with**: Python 3.11, FastAPI, Redis, Docker, Shopify Web Pixels API