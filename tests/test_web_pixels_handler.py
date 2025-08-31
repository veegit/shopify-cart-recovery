import pytest
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime

from apps.web_pixels_handler.main import app
from apps.web_pixels_handler.models import (
    ClickedEventModel, InputChangedEventModel, FormSubmittedEventModel,
    WebPixelEventProcessor
)


class TestWebPixelsHandler:
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
    def sample_click_payload(self):
        return {
            "clientX": 150,
            "clientY": 250,
            "element_id": "add-to-cart-btn",
            "element_class": "btn btn-primary",
            "element_tag": "button",
            "element_text": "Add to Cart",
            "target_selector": "button#add-to-cart-btn",
            "page_x": 150,
            "page_y": 350,
            "url": "https://test-shop.myshopify.com/products/test-product"
        }
    
    @pytest.fixture
    def sample_input_payload(self):
        return {
            "element_id": "email-input",
            "element_name": "email",
            "element_type": "email",
            "element_value": "test@example.com",
            "previous_value": "",
            "element_selector": "input#email-input",
            "form_id": "newsletter-form",
            "url": "https://test-shop.myshopify.com/pages/contact"
        }
    
    @pytest.fixture
    def sample_form_payload(self):
        return {
            "form_id": "checkout-form",
            "form_name": "checkout",
            "form_action": "/checkout",
            "form_method": "POST",
            "field_count": 5,
            "filled_fields": 4,
            "form_selector": "form#checkout-form",
            "submission_method": "click",
            "url": "https://test-shop.myshopify.com/checkout"
        }
    
    @pytest.fixture
    def session_headers(self):
        return {
            "X-Session-ID": "test_session_123",
            "X-Customer-ID": "customer_456",
            "X-Shop-Domain": "test-shop.myshopify.com",
            "Content-Type": "application/json"
        }
    
    @patch('apps.web_pixels_handler.main.redis_client')
    def test_click_event_valid(self, mock_redis, client, sample_click_payload, session_headers):
        mock_redis.publish_event = AsyncMock(return_value=True)
        
        response = client.post(
            "/pixels/clicked",
            json=sample_click_payload,
            headers=session_headers
        )
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "success"
        assert "event_id" in response_data
        assert "session_id" in response_data
        
        # Verify Redis publishing
        mock_redis.publish_event.assert_called_once()
        call_args = mock_redis.publish_event.call_args
        channel = call_args[0][0]
        event_data = call_args[0][1]
        
        assert channel == "click_events"
        assert event_data["event_type"] == "clicked"
        assert event_data["session_id"] == "test_session_123"
        assert event_data["customer_id"] == "customer_456"
    
    def test_click_event_invalid_coordinates(self, client, session_headers):
        invalid_payload = {
            "clientX": -10,  # Invalid negative coordinate
            "clientY": 250,
            "element_tag": "button",
            "url": "https://test-shop.myshopify.com/products/test"
        }
        
        response = client.post(
            "/pixels/clicked",
            json=invalid_payload,
            headers=session_headers
        )
        
        assert response.status_code == 400
        assert "Invalid event data" in response.json()["detail"]
    
    @patch('apps.web_pixels_handler.main.redis_client')
    def test_input_changed_event(self, mock_redis, client, sample_input_payload, session_headers):
        mock_redis.publish_event = AsyncMock(return_value=True)
        
        response = client.post(
            "/pixels/input_changed",
            json=sample_input_payload,
            headers=session_headers
        )
        
        assert response.status_code == 200
        
        # Verify Redis publishing to dom_events channel
        mock_redis.publish_event.assert_called_once()
        call_args = mock_redis.publish_event.call_args
        channel = call_args[0][0]
        
        assert channel == "dom_events"
    
    @patch('apps.web_pixels_handler.main.redis_client')
    def test_form_submitted_event(self, mock_redis, client, sample_form_payload, session_headers):
        mock_redis.publish_event = AsyncMock(return_value=True)
        
        response = client.post(
            "/pixels/form_submitted",
            json=sample_form_payload,
            headers=session_headers
        )
        
        assert response.status_code == 200
        
        # Verify Redis publishing to form_events channel
        mock_redis.publish_event.assert_called_once()
        call_args = mock_redis.publish_event.call_args
        channel = call_args[0][0]
        event_data = call_args[0][1]
        
        assert channel == "form_events"
        assert event_data["data"]["field_count"] == 5
        assert event_data["data"]["filled_fields"] == 4
    
    def test_session_creation_without_header(self, client, sample_click_payload):
        with patch('apps.web_pixels_handler.main.redis_client') as mock_redis:
            mock_redis.publish_event = AsyncMock(return_value=True)
            
            response = client.post(
                "/pixels/clicked",
                json=sample_click_payload
            )
            
            assert response.status_code == 200
            response_data = response.json()
            
            # Should auto-generate session ID
            assert "session_id" in response_data
            assert response_data["session_id"] is not None
    
    @patch('apps.web_pixels_handler.main.rate_limiter')
    def test_rate_limiting(self, mock_limiter, client, sample_click_payload, session_headers):
        mock_limiter.is_allowed.return_value = False
        
        response = client.post(
            "/pixels/clicked",
            json=sample_click_payload,
            headers=session_headers
        )
        
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]
    
    def test_cors_preflight(self, client):
        response = client.options("/pixels/clicked")
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
    
    def test_health_endpoint(self, client):
        with patch('apps.web_pixels_handler.main.redis_client') as mock_redis:
            mock_redis.health_check = AsyncMock(return_value=True)
            
            response = client.get("/health")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"
            assert data["redis_connection"] is True
            assert "active_sessions" in data
            assert "performance_metrics" in data
    
    def test_metrics_endpoint(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert "sessions" in data
        assert "performance" in data
        assert "rate_limiting" in data


class TestWebPixelEventModels:
    def test_clicked_event_model_validation(self):
        valid_data = {
            "clientX": 100,
            "clientY": 200,
            "element_tag": "button",
            "url": "https://test.com"
        }
        
        event = ClickedEventModel(**valid_data)
        assert event.clientX == 100
        assert event.clientY == 200
        assert event.element_tag == "button"
    
    def test_clicked_event_invalid_coordinates(self):
        invalid_data = {
            "clientX": -50,  # Invalid negative
            "clientY": 200,
            "element_tag": "button",
            "url": "https://test.com"
        }
        
        with pytest.raises(ValueError):
            ClickedEventModel(**invalid_data)
    
    def test_input_changed_model_validation(self):
        valid_data = {
            "element_type": "email",
            "element_value": "test@example.com",
            "url": "https://test.com"
        }
        
        event = InputChangedEventModel(**valid_data)
        assert event.element_type == "email"
        assert event.element_value == "test@example.com"
    
    def test_form_submitted_model_validation(self):
        valid_data = {
            "field_count": 5,
            "filled_fields": 3,
            "url": "https://test.com"
        }
        
        event = FormSubmittedEventModel(**valid_data)
        assert event.field_count == 5
        assert event.filled_fields == 3
        assert event.form_method == "POST"  # Default value
    
    def test_form_submitted_invalid_field_count(self):
        invalid_data = {
            "field_count": 3,
            "filled_fields": 5,  # More than total fields
            "url": "https://test.com"
        }
        
        with pytest.raises(ValueError):
            FormSubmittedEventModel(**invalid_data)
    
    def test_event_to_redis_format(self):
        event = ClickedEventModel(
            clientX=100,
            clientY=200,
            element_tag="button",
            url="https://test.com",
            session_id="test_session",
            customer_id="test_customer"
        )
        
        redis_event = event.to_redis_event()
        
        assert redis_event["event_type"] == "clickedevent"
        assert redis_event["session_id"] == "test_session"
        assert redis_event["customer_id"] == "test_customer"
        assert redis_event["source"] == "web_pixels"
        assert "data" in redis_event
        assert redis_event["data"]["clientX"] == 100


class TestWebPixelEventProcessor:
    @pytest.fixture
    def processor(self):
        return WebPixelEventProcessor()
    
    def test_validate_click_payload(self, processor):
        payload = {
            "clientX": 150,
            "clientY": 250,
            "element_tag": "button",
            "url": "https://test.com"
        }
        
        event = processor.validate_payload("clicked", payload)
        assert isinstance(event, ClickedEventModel)
        assert event.clientX == 150
        assert event.clientY == 250
    
    def test_validate_invalid_event_type(self, processor):
        payload = {"url": "https://test.com"}
        
        with pytest.raises(ValueError, match="Unknown event type"):
            processor.validate_payload("invalid_type", payload)
    
    def test_enrich_event_with_session_context(self, processor):
        payload = {
            "clientX": 100,
            "clientY": 200,
            "element_tag": "div",
            "url": "https://test.com"
        }
        
        event = processor.validate_payload("clicked", payload)
        
        session_context = {
            "session_id": "test_session_456",
            "customer_id": "customer_789",
            "shop_domain": "test-shop.myshopify.com"
        }
        
        enriched_event = processor.enrich_event(event, session_context)
        
        assert enriched_event.session_id == "test_session_456"
        assert enriched_event.customer_id == "customer_789"
        assert enriched_event.shop_domain == "test-shop.myshopify.com"
        assert enriched_event.sequence_number == 1
    
    def test_sequence_number_increment(self, processor):
        payload = {
            "clientX": 100,
            "clientY": 200,
            "element_tag": "button",
            "url": "https://test.com"
        }
        
        session_context = {"session_id": "test_session"}
        
        # First event
        event1 = processor.validate_payload("clicked", payload)
        enriched1 = processor.enrich_event(event1, session_context)
        assert enriched1.sequence_number == 1
        
        # Second event
        event2 = processor.validate_payload("clicked", payload)
        enriched2 = processor.enrich_event(event2, session_context)
        assert enriched2.sequence_number == 2
    
    def test_deduplicate_event(self, processor):
        payload = {
            "clientX": 100,
            "clientY": 200,
            "element_tag": "button",
            "url": "https://test.com"
        }
        
        session_context = {"session_id": "test_session"}
        
        event1 = processor.validate_payload("clicked", payload)
        enriched1 = processor.enrich_event(event1, session_context)
        
        # First occurrence should be allowed
        assert processor.deduplicate_event(enriched1) is True
        
        # Duplicate should be blocked
        assert processor.deduplicate_event(enriched1) is False
    
    def test_process_event_end_to_end(self, processor):
        payload = {
            "clientX": 100,
            "clientY": 200,
            "element_tag": "button",
            "element_id": "checkout-btn",
            "url": "https://test.com/checkout"
        }
        
        session_context = {
            "session_id": "test_session_123",
            "customer_id": "customer_456"
        }
        
        redis_event = processor.process_event("clicked", payload, session_context)
        
        assert redis_event["event_type"] == "clickedevent"
        assert redis_event["session_id"] == "test_session_123"
        assert redis_event["customer_id"] == "customer_456"
        assert redis_event["source"] == "web_pixels"
        assert redis_event["data"]["clientX"] == 100
        assert redis_event["data"]["element_id"] == "checkout-btn"


class TestSessionManagement:
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @patch('apps.web_pixels_handler.main.redis_client')
    def test_session_tracking_across_events(self, mock_redis, client):
        mock_redis.publish_event = AsyncMock(return_value=True)
        
        session_id = "persistent_session_123"
        headers = {
            "X-Session-ID": session_id,
            "X-Customer-ID": "customer_789"
        }
        
        # Send multiple events with same session
        click_payload = {
            "clientX": 100,
            "clientY": 200,
            "element_tag": "button",
            "url": "https://test.com"
        }
        
        input_payload = {
            "element_type": "email",
            "element_value": "test@example.com",
            "url": "https://test.com"
        }
        
        # First event
        response1 = client.post("/pixels/clicked", json=click_payload, headers=headers)
        assert response1.status_code == 200
        assert response1.json()["session_id"] == session_id
        
        # Second event
        response2 = client.post("/pixels/input_changed", json=input_payload, headers=headers)
        assert response2.status_code == 200
        assert response2.json()["session_id"] == session_id
        
        # Verify both events were published
        assert mock_redis.publish_event.call_count == 2
    
    @patch('apps.web_pixels_handler.main.redis_client')  
    def test_session_cleanup(self, mock_redis, client):
        mock_redis.publish_event = AsyncMock(return_value=True)
        
        # Trigger session cleanup by calling health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        
        # Should not raise any errors during cleanup


@pytest.mark.asyncio
async def test_performance_metrics_tracking():
    from apps.web_pixels_handler.main import update_performance_metrics, performance_metrics
    
    # Reset metrics
    performance_metrics["total_events"] = 0
    performance_metrics["processing_times"] = []
    
    # Simulate processing times
    update_performance_metrics(0.05)  # 50ms
    update_performance_metrics(0.03)  # 30ms
    update_performance_metrics(0.08)  # 80ms
    
    assert performance_metrics["total_events"] == 3
    assert len(performance_metrics["processing_times"]) == 3
    assert performance_metrics["avg_processing_time"] > 0


def test_rate_limiter():
    from apps.web_pixels_handler.main import RateLimiter
    
    limiter = RateLimiter(max_requests=3, window_seconds=60)
    
    client_id = "192.168.1.1"
    
    # First 3 requests should be allowed
    assert limiter.is_allowed(client_id) is True
    assert limiter.is_allowed(client_id) is True
    assert limiter.is_allowed(client_id) is True
    
    # Fourth request should be blocked
    assert limiter.is_allowed(client_id) is False
    
    # Different client should be allowed
    assert limiter.is_allowed("192.168.1.2") is True