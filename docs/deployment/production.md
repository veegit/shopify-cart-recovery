# Production Deployment Guide

Comprehensive guide for deploying the Shopify Cart Recovery dual-stream architecture in production environments.

## 🏗️ Production Architecture

### Multi-Service Deployment Structure

```
┌─────────────────────────────────────────────────────┐
│                 Load Balancer                        │
│                 (nginx/HAProxy)                      │
└─────────┬─────────────────────────────┬─────────────┘
          │                             │
    ┌─────▼──────┐              ┌──────▼──────┐
    │  Webhook   │              │ Web Pixels  │
    │  Handlers  │              │  Handlers   │
    │ (Port 8001)│              │ (Port 8002) │
    │            │              │             │
    │ ┌────────┐ │              │ ┌─────────┐ │
    │ │Service │ │              │ │Service  │ │
    │ │   1    │ │              │ │   1     │ │
    │ └────────┘ │              │ └─────────┘ │
    │ ┌────────┐ │              │ ┌─────────┐ │
    │ │Service │ │              │ │Service  │ │
    │ │   2    │ │              │ │   2     │ │
    │ └────────┘ │              │ └─────────┘ │
    └─────┬──────┘              └──────┬──────┘
          │                            │
          └────────────┬─────────────────┘
                       │
            ┌─────────▼──────────┐
            │    Redis Cluster    │
            │   (Pub/Sub + Cache) │
            │                    │
            │  ┌─────┐  ┌─────┐  │
            │  │Node1│  │Node2│  │
            │  └─────┘  └─────┘  │
            │  ┌─────┐           │
            │  │Node3│           │
            │  └─────┘           │
            └─────────┬──────────┘
                      │
            ┌─────────▼──────────┐
            │  Event Processors  │
            │                   │
            │ ┌────────────────┐ │
            │ │   Processor 1  │ │
            │ └────────────────┘ │
            │ ┌────────────────┐ │
            │ │   Processor 2  │ │
            │ └────────────────┘ │
            └────────────────────┘
```

## 🚀 Deployment Options

### Option 1: Docker Compose Production

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  redis-node1:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf --cluster-node-timeout 5000 --appendonly yes --port 7000
    volumes:
      - redis_data_1:/data
    ports:
      - "7000:7000"
    networks:
      - redis_cluster

  redis-node2:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf --cluster-node-timeout 5000 --appendonly yes --port 7001
    volumes:
      - redis_data_2:/data
    ports:
      - "7001:7001"
    networks:
      - redis_cluster

  redis-node3:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf --cluster-node-timeout 5000 --appendonly yes --port 7002
    volumes:
      - redis_data_3:/data
    ports:
      - "7002:7002"
    networks:
      - redis_cluster

  webhook-handler-1:
    build: .
    image: shopify-cart-recovery:latest
    environment:
      - REDIS_HOST=redis-node1,redis-node2,redis-node3
      - REDIS_PORT=7000,7001,7002
      - APP_ENV=production
      - SERVICE_NAME=webhook-handler
    env_file:
      - .env.production
    command: python main.py webhook-handler
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - app_network
      - redis_cluster

  webhook-handler-2:
    extends: webhook-handler-1
    
  pixels-handler-1:
    build: .
    image: shopify-cart-recovery:latest
    environment:
      - REDIS_HOST=redis-node1,redis-node2,redis-node3
      - REDIS_PORT=7000,7001,7002
      - APP_ENV=production
      - SERVICE_NAME=web-pixels-handler
    env_file:
      - .env.production
    command: python main.py web-pixels-handler
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - app_network
      - redis_cluster

  pixels-handler-2:
    extends: pixels-handler-1

  pixels-handler-3:
    extends: pixels-handler-1

  event-processor-1:
    build: .
    image: shopify-cart-recovery:latest
    environment:
      - REDIS_HOST=redis-node1,redis-node2,redis-node3
      - REDIS_PORT=7000,7001,7002
      - APP_ENV=production
      - SERVICE_NAME=event-processor
    env_file:
      - .env.production
    command: python main.py event-processor
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
    networks:
      - redis_cluster

  event-processor-2:
    extends: event-processor-1

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
    depends_on:
      - webhook-handler-1
      - webhook-handler-2
      - pixels-handler-1
      - pixels-handler-2
      - pixels-handler-3
    networks:
      - app_network
    restart: unless-stopped

volumes:
  redis_data_1:
  redis_data_2:
  redis_data_3:

networks:
  app_network:
    driver: bridge
  redis_cluster:
    driver: bridge
```

### Option 2: Kubernetes Deployment

Create Kubernetes manifests:

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: shopify-cart-recovery

---
# k8s/redis-cluster.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis-cluster
  namespace: shopify-cart-recovery
spec:
  serviceName: redis-cluster
  replicas: 3
  selector:
    matchLabels:
      app: redis-cluster
  template:
    metadata:
      labels:
        app: redis-cluster
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        command:
        - redis-server
        args:
        - --cluster-enabled yes
        - --cluster-config-file nodes.conf
        - --cluster-node-timeout 5000
        - --appendonly yes
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        volumeMounts:
        - name: redis-data
          mountPath: /data
  volumeClaimTemplates:
  - metadata:
      name: redis-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi

---
# k8s/webhook-handler.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webhook-handler
  namespace: shopify-cart-recovery
spec:
  replicas: 2
  selector:
    matchLabels:
      app: webhook-handler
  template:
    metadata:
      labels:
        app: webhook-handler
    spec:
      containers:
      - name: webhook-handler
        image: shopify-cart-recovery:latest
        ports:
        - containerPort: 8000
        env:
        - name: APP_ENV
          value: "production"
        - name: SERVICE_NAME
          value: "webhook-handler"
        - name: REDIS_HOST
          value: "redis-cluster-0.redis-cluster,redis-cluster-1.redis-cluster,redis-cluster-2.redis-cluster"
        - name: REDIS_PORT
          value: "6379"
        envFrom:
        - secretRef:
            name: shopify-secrets
        command: ["python", "main.py", "webhook-handler"]
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
# k8s/pixels-handler.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pixels-handler
  namespace: shopify-cart-recovery
spec:
  replicas: 3
  selector:
    matchLabels:
      app: pixels-handler
  template:
    metadata:
      labels:
        app: pixels-handler
    spec:
      containers:
      - name: pixels-handler
        image: shopify-cart-recovery:latest
        ports:
        - containerPort: 8000
        env:
        - name: APP_ENV
          value: "production"
        - name: SERVICE_NAME
          value: "web-pixels-handler"
        - name: REDIS_HOST
          value: "redis-cluster-0.redis-cluster,redis-cluster-1.redis-cluster,redis-cluster-2.redis-cluster"
        - name: REDIS_PORT
          value: "6379"
        envFrom:
        - secretRef:
            name: shopify-secrets
        command: ["python", "main.py", "web-pixels-handler"]
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"

---
# k8s/event-processor.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: event-processor
  namespace: shopify-cart-recovery
spec:
  replicas: 2
  selector:
    matchLabels:
      app: event-processor
  template:
    metadata:
      labels:
        app: event-processor
    spec:
      containers:
      - name: event-processor
        image: shopify-cart-recovery:latest
        env:
        - name: APP_ENV
          value: "production"
        - name: SERVICE_NAME
          value: "event-processor"
        - name: REDIS_HOST
          value: "redis-cluster-0.redis-cluster,redis-cluster-1.redis-cluster,redis-cluster-2.redis-cluster"
        - name: REDIS_PORT
          value: "6379"
        envFrom:
        - secretRef:
            name: shopify-secrets
        command: ["python", "main.py", "event-processor"]
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"

---
# k8s/services.yaml
apiVersion: v1
kind: Service
metadata:
  name: webhook-handler-service
  namespace: shopify-cart-recovery
spec:
  selector:
    app: webhook-handler
  ports:
  - port: 8001
    targetPort: 8000
  type: ClusterIP

---
apiVersion: v1
kind: Service
metadata:
  name: pixels-handler-service
  namespace: shopify-cart-recovery
spec:
  selector:
    app: pixels-handler
  ports:
  - port: 8002
    targetPort: 8000
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: shopify-cart-recovery-ingress
  namespace: shopify-cart-recovery
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - your-domain.com
    secretName: shopify-cart-recovery-tls
  rules:
  - host: your-domain.com
    http:
      paths:
      - path: /webhooks
        pathType: Prefix
        backend:
          service:
            name: webhook-handler-service
            port:
              number: 8001
      - path: /pixels
        pathType: Prefix
        backend:
          service:
            name: pixels-handler-service
            port:
              number: 8002
```

## 🔧 Environment Configuration

### Production Environment Variables

Create `.env.production`:

```bash
# Application Environment
APP_ENV=production
APP_HOST=0.0.0.0
APP_PORT=8000

# Redis Cluster Configuration
REDIS_HOST=redis-node1,redis-node2,redis-node3
REDIS_PORT=7000,7001,7002
REDIS_PASSWORD=your_secure_redis_password
REDIS_DB=0
REDIS_CLUSTER_MODE=true

# Shopify Integration
SHOPIFY_API_KEY=your_production_api_key
SHOPIFY_API_SECRET=your_production_api_secret
SHOPIFY_WEBHOOK_SECRET=your_production_webhook_secret
SHOPIFY_APP_URL=https://your-domain.com

# Web Pixels Configuration
WEB_PIXELS_ENDPOINT=https://your-domain.com/pixels

# Performance Settings
MAX_BATCH_SIZE=50
BATCH_TIMEOUT_MS=1000
MAX_RETRY_ATTEMPTS=3
WEBHOOK_HANDLER_WORKERS=4
PIXELS_HANDLER_WORKERS=6

# Security Settings
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CORS_ORIGINS=https://your-shopify-store.myshopify.com,https://custom-domain.com
RATE_LIMIT_PER_IP=1000
RATE_LIMIT_WINDOW=60

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/shopify-cart-recovery.log
ENABLE_ACCESS_LOGS=true

# Monitoring & Alerting
ENABLE_METRICS=true
METRICS_ENDPOINT=/metrics
HEALTH_CHECK_TIMEOUT=30
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

# SSL/TLS
SSL_CERT_PATH=/etc/ssl/certs/server.crt
SSL_KEY_PATH=/etc/ssl/private/server.key
SSL_VERIFY_PEER=true

# Database (if using persistent storage)
DATABASE_URL=postgresql://user:pass@host:5432/shopify_cart_recovery
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
```

### Secrets Management

#### Using Docker Secrets

```bash
# Create secrets
echo "your_shopify_api_key" | docker secret create shopify_api_key -
echo "your_webhook_secret" | docker secret create webhook_secret -
echo "your_redis_password" | docker secret create redis_password -

# Reference in docker-compose.prod.yml
secrets:
  - shopify_api_key
  - webhook_secret
  - redis_password
```

#### Using Kubernetes Secrets

```bash
# Create Kubernetes secrets
kubectl create secret generic shopify-secrets \
  --from-literal=SHOPIFY_API_KEY='your_api_key' \
  --from-literal=SHOPIFY_API_SECRET='your_api_secret' \
  --from-literal=SHOPIFY_WEBHOOK_SECRET='your_webhook_secret' \
  --from-literal=REDIS_PASSWORD='your_redis_password' \
  -n shopify-cart-recovery

# Verify secret creation
kubectl get secrets -n shopify-cart-recovery
```

#### Using HashiCorp Vault

```python
# vault_config.py
import hvac
import os

class VaultConfig:
    def __init__(self):
        self.client = hvac.Client(url=os.getenv('VAULT_URL'))
        self.client.token = os.getenv('VAULT_TOKEN')
    
    def get_shopify_config(self):
        secret = self.client.secrets.kv.v2.read_secret_version(
            path='shopify-cart-recovery'
        )
        return secret['data']['data']

# Usage in main application
vault = VaultConfig()
secrets = vault.get_shopify_config()
SHOPIFY_API_KEY = secrets['api_key']
SHOPIFY_WEBHOOK_SECRET = secrets['webhook_secret']
```

## 🔒 Security Configuration

### SSL/TLS Setup

#### Nginx SSL Configuration

```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream webhook_handlers {
        least_conn;
        server webhook-handler-1:8000 max_fails=3 fail_timeout=30s;
        server webhook-handler-2:8000 max_fails=3 fail_timeout=30s;
    }

    upstream pixels_handlers {
        least_conn;
        server pixels-handler-1:8000 max_fails=3 fail_timeout=30s;
        server pixels-handler-2:8000 max_fails=3 fail_timeout=30s;
        server pixels-handler-3:8000 max_fails=3 fail_timeout=30s;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=webhook_limit:10m rate=100r/m;
    limit_req_zone $binary_remote_addr zone=pixels_limit:10m rate=1000r/m;

    server {
        listen 80;
        server_name your-domain.com www.your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com www.your-domain.com;

        # SSL Configuration
        ssl_certificate /etc/ssl/certs/server.crt;
        ssl_certificate_key /etc/ssl/private/server.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options DENY always;
        add_header X-Content-Type-Options nosniff always;
        add_header X-XSS-Protection "1; mode=block" always;

        # Webhook endpoints
        location /webhooks/ {
            limit_req zone=webhook_limit burst=50 nodelay;
            proxy_pass http://webhook_handlers;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Shopify-specific headers
            proxy_pass_header X-Shopify-Topic;
            proxy_pass_header X-Shopify-Shop-Domain;
            proxy_pass_header X-Shopify-Hmac-Sha256;
            proxy_pass_header X-Shopify-Timestamp;
        }

        # Web Pixels endpoints
        location /pixels/ {
            limit_req zone=pixels_limit burst=200 nodelay;
            proxy_pass http://pixels_handlers;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # CORS for browser requests
            add_header Access-Control-Allow-Origin "https://your-shopify-store.myshopify.com" always;
            add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
            add_header Access-Control-Allow-Headers "Content-Type, X-Session-ID, X-Customer-ID, X-Shop-Domain" always;

            if ($request_method = 'OPTIONS') {
                add_header Access-Control-Max-Age 86400;
                add_header Content-Type text/plain;
                add_header Content-Length 0;
                return 204;
            }
        }

        # Health checks
        location /health {
            access_log off;
            proxy_pass http://webhook_handlers/health;
        }
    }
}
```

### Firewall Configuration

```bash
#!/bin/bash
# setup_firewall.sh

# Allow SSH
ufw allow ssh

# Allow HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Allow Redis cluster communication (internal only)
ufw allow from 10.0.0.0/8 to any port 7000:7002

# Block direct access to application ports
ufw deny 8000:8002/tcp

# Enable firewall
ufw --force enable

echo "Firewall configured for production deployment"
```

## 📊 Scaling Considerations

### Horizontal Scaling Configuration

#### Auto-scaling with Docker Compose

```bash
# Scale services based on load
docker-compose -f docker-compose.prod.yml up -d --scale pixels-handler=5
docker-compose -f docker-compose.prod.yml up -d --scale webhook-handler=3
docker-compose -f docker-compose.prod.yml up -d --scale event-processor=3
```

#### Kubernetes Horizontal Pod Autoscaler

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: pixels-handler-hpa
  namespace: shopify-cart-recovery
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: pixels-handler
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: webhook-handler-hpa
  namespace: shopify-cart-recovery
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: webhook-handler
  minReplicas: 2
  maxReplicas: 8
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60
```

### Performance Optimization

#### Redis Cluster Optimization

```bash
# redis-cluster-setup.sh
#!/bin/bash

# Create Redis cluster
redis-cli --cluster create \
    redis-node1:7000 \
    redis-node2:7001 \
    redis-node3:7002 \
    --cluster-replicas 0

# Configure memory optimization
redis-cli -h redis-node1 -p 7000 CONFIG SET maxmemory-policy allkeys-lru
redis-cli -h redis-node2 -p 7001 CONFIG SET maxmemory-policy allkeys-lru
redis-cli -h redis-node3 -p 7002 CONFIG SET maxmemory-policy allkeys-lru

# Enable Redis persistence
redis-cli -h redis-node1 -p 7000 CONFIG SET save "900 1 300 10 60 10000"
redis-cli -h redis-node2 -p 7001 CONFIG SET save "900 1 300 10 60 10000"
redis-cli -h redis-node3 -p 7002 CONFIG SET save "900 1 300 10 60 10000"

echo "Redis cluster configured and optimized"
```

#### Application Performance Tuning

```python
# performance_config.py
import uvicorn
from multiprocessing import cpu_count

# Production ASGI configuration
class ProductionConfig:
    @staticmethod
    def get_uvicorn_config(service_type):
        base_config = {
            "host": "0.0.0.0",
            "port": 8000,
            "workers": cpu_count(),
            "worker_class": "uvicorn.workers.UvicornWorker",
            "max_requests": 1000,
            "max_requests_jitter": 100,
            "preload_app": True,
            "timeout": 30,
            "keepalive": 2
        }
        
        # Service-specific optimizations
        if service_type == "web-pixels-handler":
            # Higher concurrency for DOM events
            base_config.update({
                "workers": cpu_count() * 2,
                "worker_connections": 2000,
                "max_requests": 2000
            })
        elif service_type == "webhook-handler":
            # Optimized for webhook processing
            base_config.update({
                "workers": cpu_count(),
                "worker_connections": 1000,
                "max_requests": 1000
            })
        
        return base_config
```

## 📈 Monitoring & Alerting

### Production Monitoring Stack

#### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "shopify_cart_recovery_rules.yml"

scrape_configs:
  - job_name: 'webhook-handlers'
    static_configs:
      - targets: ['webhook-handler-1:8000', 'webhook-handler-2:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'pixels-handlers'
    static_configs:
      - targets: ['pixels-handler-1:8000', 'pixels-handler-2:8000', 'pixels-handler-3:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'redis-cluster'
    static_configs:
      - targets: ['redis-node1:7000', 'redis-node2:7001', 'redis-node3:7002']

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
```

#### Alert Rules

```yaml
# shopify_cart_recovery_rules.yml
groups:
  - name: shopify_cart_recovery
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time"
          description: "95th percentile response time is {{ $value }}s"

      - alert: RedisConnectionDown
        expr: redis_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Redis connection is down"

      - alert: HighCPUUsage
        expr: rate(container_cpu_usage_seconds_total[5m]) > 0.8
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected"

      - alert: LowEventProcessingRate
        expr: rate(events_processed_total[5m]) < 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Low event processing rate"
          description: "Processing rate is {{ $value }} events per second"
```

### Health Check Endpoints

```python
# Enhanced health checks for production
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
import asyncio
import time

app = FastAPI()

@app.get("/health")
async def health_check():
    checks = {}
    overall_healthy = True
    
    # Redis connectivity
    try:
        redis_client = await get_redis_client()
        await redis_client.ping()
        checks["redis"] = {"status": "healthy", "latency_ms": 0}
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False
    
    # Application metrics
    checks["application"] = {
        "status": "healthy",
        "uptime_seconds": time.time() - start_time,
        "version": "1.0.0"
    }
    
    # Memory usage
    try:
        import psutil
        memory = psutil.virtual_memory()
        checks["system"] = {
            "memory_percent": memory.percent,
            "cpu_percent": psutil.cpu_percent(),
            "disk_percent": psutil.disk_usage('/').percent
        }
        
        if memory.percent > 90:
            overall_healthy = False
    except ImportError:
        pass
    
    status_code = status.HTTP_200_OK if overall_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(
        content={
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks
        },
        status_code=status_code
    )

@app.get("/ready")
async def readiness_check():
    # Check if service is ready to accept traffic
    try:
        # Verify critical dependencies
        redis_client = await get_redis_client()
        await redis_client.ping()
        
        return {"status": "ready"}
    except Exception as e:
        return JSONResponse(
            content={"status": "not ready", "reason": str(e)},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )
```

## 🚀 Deployment Commands

### Docker Compose Deployment

```bash
#!/bin/bash
# deploy.sh

set -e

echo "🚀 Starting production deployment..."

# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Build application image
docker build -t shopify-cart-recovery:latest .

# Initialize Redis cluster
docker-compose -f docker-compose.prod.yml up -d redis-node1 redis-node2 redis-node3
sleep 30
docker exec redis-node1 redis-cli --cluster create redis-node1:7000 redis-node2:7001 redis-node3:7002 --cluster-replicas 0 --cluster-yes

# Start application services
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
for i in {1..30}; do
    if curl -f http://localhost/health; then
        echo "✅ All services are healthy"
        break
    fi
    sleep 10
done

echo "🎉 Deployment completed successfully"
```

### Kubernetes Deployment

```bash
#!/bin/bash
# k8s-deploy.sh

set -e

echo "🚀 Deploying to Kubernetes..."

# Create namespace
kubectl apply -f k8s/namespace.yaml

# Apply secrets (ensure secrets are created first)
kubectl apply -f k8s/secrets.yaml

# Deploy Redis cluster
kubectl apply -f k8s/redis-cluster.yaml

# Wait for Redis to be ready
kubectl wait --for=condition=ready pod -l app=redis-cluster -n shopify-cart-recovery --timeout=300s

# Deploy application services
kubectl apply -f k8s/webhook-handler.yaml
kubectl apply -f k8s/pixels-handler.yaml
kubectl apply -f k8s/event-processor.yaml

# Deploy services and ingress
kubectl apply -f k8s/services.yaml
kubectl apply -f k8s/ingress.yaml

# Deploy monitoring
kubectl apply -f k8s/hpa.yaml

# Wait for deployments
kubectl rollout status deployment/webhook-handler -n shopify-cart-recovery
kubectl rollout status deployment/pixels-handler -n shopify-cart-recovery
kubectl rollout status deployment/event-processor -n shopify-cart-recovery

echo "✅ Kubernetes deployment completed"

# Show service status
kubectl get pods -n shopify-cart-recovery
kubectl get services -n shopify-cart-recovery
kubectl get ingress -n shopify-cart-recovery
```

## 🔄 Backup & Recovery

### Redis Backup Strategy

```bash
#!/bin/bash
# backup_redis.sh

BACKUP_DIR="/var/backups/redis"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup each Redis node
for node in redis-node1:7000 redis-node2:7001 redis-node3:7002; do
    host=$(echo $node | cut -d: -f1)
    port=$(echo $node | cut -d: -f2)
    
    echo "Backing up $host:$port..."
    
    # Create backup
    redis-cli -h $host -p $port --rdb $BACKUP_DIR/${host}_${port}_${TIMESTAMP}.rdb
    
    # Compress backup
    gzip $BACKUP_DIR/${host}_${port}_${TIMESTAMP}.rdb
done

# Clean old backups (keep last 7 days)
find $BACKUP_DIR -name "*.rdb.gz" -mtime +7 -delete

echo "Redis backup completed: $BACKUP_DIR"
```

### Application Configuration Backup

```bash
#!/bin/bash
# backup_config.sh

BACKUP_DIR="/var/backups/config"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup environment files
cp .env.production $BACKUP_DIR/env_${TIMESTAMP}

# Backup Docker Compose files
cp docker-compose.prod.yml $BACKUP_DIR/docker-compose_${TIMESTAMP}.yml

# Backup Nginx config
cp nginx.conf $BACKUP_DIR/nginx_${TIMESTAMP}.conf

# Backup SSL certificates
cp -r /etc/ssl/certs $BACKUP_DIR/ssl_${TIMESTAMP}/

# Create archive
tar -czf $BACKUP_DIR/config_backup_${TIMESTAMP}.tar.gz -C $BACKUP_DIR .

echo "Configuration backup completed: $BACKUP_DIR/config_backup_${TIMESTAMP}.tar.gz"
```

This production deployment guide provides comprehensive coverage for deploying the dual-stream Shopify Cart Recovery system in production environments with proper scaling, security, monitoring, and backup strategies.