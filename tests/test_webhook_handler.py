import pytest
import json
import hmac
import hashlib
import time
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
import asyncio

from apps.shopify_webhook_handler.main import app
from apps.shopify_webhook_handler.models import EventProcessor


class TestWebhookHandler:
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def mock_redis_client(self):
        mock_client = AsyncMock()
        mock_client.health_check.return_value = True
        mock_client.publish_event.return_value = True
        return mock_client
    
    @pytest.fixture
    def sample_cart_payload(self):
        return {
            "id": "123456789",
            "token": "cart_token_123",
            "line_items": [
                {
                    "id": 987654321,
                    "product_id": 111111,
                    "variant_id": 222222,
                    "title": "Test Product",
                    "quantity": 2,
                    "price": "29.99",
                    "sku": "TEST-SKU-001"
                }
            ],
            "total_price": "59.98",
            "total_weight": 500,
            "item_count": 2,
            "currency": "USD",
            "created_at": "2023-01-01T12:00:00Z",
            "updated_at": "2023-01-01T12:30:00Z",
            "customer": {
                "id": 555555,
                "email": "test@example.com"
            }
        }
    
    @pytest.fixture
    def sample_order_payload(self):
        return {
            "id": 987654321,
            "number": "1001",
            "line_items": [
                {
                    "id": 111111111,
                    "product_id": 222222,
                    "variant_id": 333333,
                    "title": "Test Product",
                    "quantity": 1,
                    "price": "49.99",
                    "sku": "PROD-001"
                }
            ],
            "total_price": "54.99",
            "subtotal_price": "49.99",
            "total_tax": "5.00",
            "currency": "USD",
            "financial_status": "paid",
            "fulfillment_status": "pending",
            "email": "customer@example.com",
            "created_at": "2023-01-01T14:00:00Z",
            "customer": {
                "id": 777777,
                "email": "customer@example.com"
            }
        }
    
    def generate_hmac_signature(self, payload: str, secret: str) -> str:
        return hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def test_webhook_missing_shop_domain(self, client):
        response = client.post("/webhooks/carts/create")
        assert response.status_code == 400
        assert "Missing shop domain header" in response.json()["detail"]
    
    def test_webhook_missing_topic(self, client):
        headers = {"X-Shopify-Shop-Domain": "test-shop.myshopify.com"}
        response = client.post("/webhooks/carts/create", headers=headers)
        assert response.status_code == 400
        assert "Missing webhook topic header" in response.json()["detail"]
    
    @patch('apps.shopify_webhook_handler.main.settings')
    def test_webhook_invalid_hmac(self, mock_settings, client, sample_cart_payload):
        mock_settings.shopify.webhook_secret = "test_secret"
        
        headers = {
            "X-Shopify-Shop-Domain": "test-shop.myshopify.com",
            "X-Shopify-Topic": "carts/create",
            "X-Shopify-Hmac-Sha256": "invalid_signature",
            "X-Shopify-Timestamp": str(int(time.time()))
        }
        
        response = client.post(
            "/webhooks/carts/create",
            json=sample_cart_payload,
            headers=headers
        )
        
        assert response.status_code == 401
        assert "Invalid webhook signature" in response.json()["detail"]
    
    @patch('apps.shopify_webhook_handler.main.settings')
    def test_webhook_expired_timestamp(self, mock_settings, client, sample_cart_payload):
        mock_settings.shopify.webhook_secret = "test_secret"
        payload_str = json.dumps(sample_cart_payload)
        
        headers = {
            "X-Shopify-Shop-Domain": "test-shop.myshopify.com",
            "X-Shopify-Topic": "carts/create",
            "X-Shopify-Hmac-Sha256": f"sha256={self.generate_hmac_signature(payload_str, 'test_secret')}",
            "X-Shopify-Timestamp": str(int(time.time()) - 400)  # 400 seconds ago
        }
        
        response = client.post(
            "/webhooks/carts/create",
            json=sample_cart_payload,
            headers=headers
        )
        
        assert response.status_code == 401
        assert "Invalid or expired timestamp" in response.json()["detail"]
    
    @patch('apps.shopify_webhook_handler.main.redis_client')
    @patch('apps.shopify_webhook_handler.main.settings')
    def test_webhook_valid_cart_create(self, mock_settings, mock_redis, client, sample_cart_payload):
        mock_settings.shopify.webhook_secret = "test_secret"
        mock_redis.publish_event.return_value = True
        
        payload_str = json.dumps(sample_cart_payload)
        
        headers = {
            "X-Shopify-Shop-Domain": "test-shop.myshopify.com",
            "X-Shopify-Topic": "carts/create",
            "X-Shopify-Hmac-Sha256": f"sha256={self.generate_hmac_signature(payload_str, 'test_secret')}",
            "X-Shopify-Timestamp": str(int(time.time()))
        }
        
        response = client.post(
            "/webhooks/carts/create",
            json=sample_cart_payload,
            headers=headers
        )
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "success"
        assert "event_id" in response_data
    
    @patch('apps.shopify_webhook_handler.main.redis_client')
    @patch('apps.shopify_webhook_handler.main.settings')
    def test_webhook_valid_order_create(self, mock_settings, mock_redis, client, sample_order_payload):
        mock_settings.shopify.webhook_secret = "test_secret"
        mock_redis.publish_event.return_value = True
        
        payload_str = json.dumps(sample_order_payload)
        
        headers = {
            "X-Shopify-Shop-Domain": "test-shop.myshopify.com",
            "X-Shopify-Topic": "orders/create",
            "X-Shopify-Hmac-Sha256": f"sha256={self.generate_hmac_signature(payload_str, 'test_secret')}",
            "X-Shopify-Timestamp": str(int(time.time()))
        }
        
        response = client.post(
            "/webhooks/orders/create",
            json=sample_order_payload,
            headers=headers
        )
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "success"
    
    @patch('apps.shopify_webhook_handler.main.redis_client')
    @patch('apps.shopify_webhook_handler.main.settings')
    def test_redis_publishing(self, mock_settings, mock_redis, client, sample_cart_payload):
        mock_settings.shopify.webhook_secret = "test_secret"
        mock_redis.publish_event = AsyncMock(return_value=True)
        
        payload_str = json.dumps(sample_cart_payload)
        
        headers = {
            "X-Shopify-Shop-Domain": "test-shop.myshopify.com",
            "X-Shopify-Topic": "carts/create",
            "X-Shopify-Hmac-Sha256": f"sha256={self.generate_hmac_signature(payload_str, 'test_secret')}",
            "X-Shopify-Timestamp": str(int(time.time()))
        }
        
        response = client.post(
            "/webhooks/carts/create",
            json=sample_cart_payload,
            headers=headers
        )
        
        assert response.status_code == 200
        mock_redis.publish_event.assert_called_once()
        
        # Check the published event data
        call_args = mock_redis.publish_event.call_args
        channel = call_args[0][0]
        event_data = call_args[0][1]
        
        assert channel == "cart_events"
        assert event_data["event_type"] == "cart_create"
        assert event_data["shop_domain"] == "test-shop.myshopify.com"
        assert event_data["customer_id"] == "555555"
        assert event_data["source"] == "shopify_webhook"
    
    def test_payload_too_large(self, client):
        large_payload = {"data": "x" * (1024 * 1024 + 1)}  # > 1MB
        
        headers = {
            "X-Shopify-Shop-Domain": "test-shop.myshopify.com",
            "X-Shopify-Topic": "carts/create"
        }
        
        response = client.post(
            "/webhooks/carts/create",
            json=large_payload,
            headers=headers
        )
        
        assert response.status_code == 413
        assert "Payload too large" in response.json()["detail"]
    
    def test_invalid_json_payload(self, client):
        headers = {
            "X-Shopify-Shop-Domain": "test-shop.myshopify.com",
            "X-Shopify-Topic": "carts/create",
            "X-Shopify-Hmac-Sha256": "sha256=dummy",
            "X-Shopify-Timestamp": str(int(time.time()))
        }
        
        response = client.post(
            "/webhooks/carts/create",
            data="invalid json",
            headers=headers
        )
        
        assert response.status_code == 400
        assert "Invalid JSON payload" in response.json()["detail"]
    
    def test_health_endpoint(self, client):
        with patch('apps.shopify_webhook_handler.main.redis_client') as mock_redis:
            mock_redis.health_check = AsyncMock(return_value=True)
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"
            assert response.json()["redis_connection"] is True
    
    def test_metrics_endpoint(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "rate_limiting" in response.json()
        assert "configuration" in response.json()


class TestEventProcessor:
    @pytest.fixture
    def processor(self):
        return EventProcessor()
    
    def test_cart_event_processing(self, processor):
        payload = {
            "id": "123456",
            "token": "test_token",
            "line_items": [],
            "total_price": "99.99",
            "item_count": 1,
            "currency": "USD",
            "customer": {"id": 777}
        }
        
        result = processor.process_webhook("carts/create", payload, "test-shop.myshopify.com")
        
        assert result["event_type"] == "cart_create"
        assert result["shop_domain"] == "test-shop.myshopify.com"
        assert result["customer_id"] == "777"
        assert result["source"] == "shopify_webhook"
        assert "processing_timestamp" in result
    
    def test_order_event_processing(self, processor):
        payload = {
            "id": 987654,
            "number": "1001",
            "line_items": [],
            "total_price": "149.99",
            "subtotal_price": "139.99",
            "currency": "USD",
            "financial_status": "paid",
            "customer": {"id": 888}
        }
        
        result = processor.process_webhook("orders/paid", payload, "test-shop.myshopify.com")
        
        assert result["event_type"] == "order_paid"
        assert result["customer_id"] == "888"
        assert result["data"]["financial_status"] == "paid"
    
    def test_customer_id_extraction(self, processor):
        # Test direct customer_id
        payload1 = {"customer_id": 123}
        customer_id = processor.extract_customer_id(payload1)
        assert customer_id == "123"
        
        # Test nested customer object
        payload2 = {"customer": {"id": 456}}
        customer_id = processor.extract_customer_id(payload2)
        assert customer_id == "456"
        
        # Test email fallback
        payload3 = {"email": "test@example.com"}
        customer_id = processor.extract_customer_id(payload3)
        assert customer_id == "test@example.com"
        
        # Test no customer info
        payload4 = {}
        customer_id = processor.extract_customer_id(payload4)
        assert customer_id is None
    
    def test_unsupported_webhook_topic(self, processor):
        with pytest.raises(ValueError, match="Unsupported webhook topic"):
            processor.process_webhook("unsupported/topic", {}, "test-shop.myshopify.com")
    
    def test_invalid_payload_validation(self, processor):
        invalid_payload = {
            "id": "invalid",  # Should be int for orders
            "number": "",     # Should not be empty
            "currency": "INVALID"  # Should be 3 chars
        }
        
        with pytest.raises(ValueError, match="Failed to process webhook"):
            processor.process_webhook("orders/create", invalid_payload, "test-shop.myshopify.com")


@pytest.mark.asyncio
async def test_webhook_rate_limiting():
    from apps.shopify_webhook_handler.main import WebhookRateLimiter
    
    limiter = WebhookRateLimiter(max_requests=2, window_seconds=60)
    
    # First two requests should be allowed
    assert limiter.is_allowed("test-shop.myshopify.com") is True
    assert limiter.is_allowed("test-shop.myshopify.com") is True
    
    # Third request should be blocked
    assert limiter.is_allowed("test-shop.myshopify.com") is False
    
    # Different shop should be allowed
    assert limiter.is_allowed("other-shop.myshopify.com") is True


def test_hmac_verification():
    from apps.shopify_webhook_handler.main import verify_webhook_signature
    
    payload = b'{"test": "data"}'
    secret = "test_secret"
    
    # Valid signature
    valid_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    assert verify_webhook_signature(payload, f"sha256={valid_signature}", secret) is True
    
    # Invalid signature
    assert verify_webhook_signature(payload, "sha256=invalid", secret) is False
    
    # Missing signature
    assert verify_webhook_signature(payload, None, secret) is False


def test_timestamp_verification():
    from apps.shopify_webhook_handler.main import verify_timestamp
    
    # Current timestamp should be valid
    current_time = str(int(time.time()))
    assert verify_timestamp(current_time) is True
    
    # Old timestamp should be invalid
    old_time = str(int(time.time()) - 400)
    assert verify_timestamp(old_time) is False
    
    # Invalid timestamp format
    assert verify_timestamp("invalid") is False
    assert verify_timestamp(None) is False