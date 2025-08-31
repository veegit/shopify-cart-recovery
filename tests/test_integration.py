import pytest
import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
import redis.asyncio as redis

from apps.shopify_webhook_handler.main import app as webhook_app
from apps.web_pixels_handler.main import app as pixels_app
from apps.event_processor.main import EventProcessor


class TestEndToEndIntegration:
    """Test complete flow from Web Pixels → Redis → Event Processing"""
    
    @pytest.fixture
    def webhook_client(self):
        return TestClient(webhook_app)
    
    @pytest.fixture
    def pixels_client(self):
        return TestClient(pixels_app)
    
    @pytest.fixture
    async def test_redis_client(self):
        """Create test Redis client"""
        client = redis.Redis(host='localhost', port=6379, db=15)  # Use test DB
        await client.flushdb()  # Clean test database
        yield client
        await client.flushdb()  # Clean up after test
        await client.close()
    
    @pytest.fixture
    def mock_shopify_payload(self):
        return {
            "id": "test_cart_123",
            "token": "cart_token_abc",
            "line_items": [
                {
                    "id": 999999,
                    "product_id": 111111,
                    "variant_id": 222222,
                    "title": "Integration Test Product",
                    "quantity": 1,
                    "price": "49.99",
                    "sku": "INT-TEST-001"
                }
            ],
            "total_price": "49.99",
            "item_count": 1,
            "currency": "USD",
            "created_at": "2023-01-01T12:00:00Z",
            "customer": {
                "id": 777777,
                "email": "integration@test.com"
            }
        }
    
    @pytest.fixture
    def web_pixels_payloads(self):
        return {
            "page_view": {
                "page_title": "Integration Test Product",
                "url": "https://test-shop.myshopify.com/products/test-product",
                "viewport_width": 1920,
                "viewport_height": 1080,
                "time_on_page": 15000,
                "scroll_depth": 0.75
            },
            "product_click": {
                "clientX": 200,
                "clientY": 300,
                "element_id": "add-to-cart",
                "element_class": "btn btn-primary",
                "element_tag": "button",
                "element_text": "Add to Cart",
                "url": "https://test-shop.myshopify.com/products/test-product"
            },
            "cart_form": {
                "element_type": "number",
                "element_name": "quantity",
                "element_value": "1",
                "form_id": "add-to-cart-form",
                "url": "https://test-shop.myshopify.com/products/test-product"
            },
            "checkout_form": {
                "form_id": "checkout-form",
                "form_action": "/checkout",
                "form_method": "POST",
                "field_count": 8,
                "filled_fields": 7,
                "url": "https://test-shop.myshopify.com/checkout"
            }
        }
    
    @pytest.mark.asyncio
    async def test_complete_user_journey(
        self, 
        pixels_client, 
        webhook_client, 
        test_redis_client,
        mock_shopify_payload,
        web_pixels_payloads
    ):
        """Test complete user journey: Web Pixels → Webhook → Processing"""
        
        session_id = "integration_journey_session"
        customer_id = "777777"
        
        # Mock Redis clients in both services
        with patch('apps.web_pixels_handler.main.redis_client') as mock_pixels_redis, \
             patch('apps.shopify_webhook_handler.main.redis_client') as mock_webhook_redis:
            
            # Set up Redis mocks
            mock_pixels_redis.publish_event = AsyncMock(return_value=True)
            mock_webhook_redis.publish_event = AsyncMock(return_value=True)
            
            session_headers = {
                "X-Session-ID": session_id,
                "X-Customer-ID": customer_id,
                "X-Shop-Domain": "test-shop.myshopify.com"
            }
            
            # Step 1: User views product page
            page_response = pixels_client.post(
                "/pixels/page_viewed",
                json=web_pixels_payloads["page_view"],
                headers=session_headers
            )
            assert page_response.status_code == 200
            
            # Step 2: User clicks add to cart button
            click_response = pixels_client.post(
                "/pixels/clicked",
                json=web_pixels_payloads["product_click"],
                headers=session_headers
            )
            assert click_response.status_code == 200
            
            # Step 3: User interacts with quantity form
            form_response = pixels_client.post(
                "/pixels/input_changed",
                json=web_pixels_payloads["cart_form"],
                headers=session_headers
            )
            assert form_response.status_code == 200
            
            # Step 4: Shopify webhook fires for cart creation
            webhook_headers = {
                "X-Shopify-Shop-Domain": "test-shop.myshopify.com",
                "X-Shopify-Topic": "carts/create",
                "X-Shopify-Timestamp": str(int(time.time()))
            }
            
            # Add session ID to webhook payload for correlation
            webhook_payload = {
                **mock_shopify_payload,
                "session_id": session_id
            }
            
            with patch('apps.shopify_webhook_handler.main.settings') as mock_settings:
                mock_settings.shopify.webhook_secret = "test_secret"
                
                # Generate valid HMAC
                import hmac
                import hashlib
                payload_str = json.dumps(webhook_payload)
                signature = hmac.new(
                    "test_secret".encode('utf-8'),
                    payload_str.encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()
                
                webhook_headers["X-Shopify-Hmac-Sha256"] = f"sha256={signature}"
                
                webhook_response = webhook_client.post(
                    "/webhooks/carts/create",
                    json=webhook_payload,
                    headers=webhook_headers
                )
                assert webhook_response.status_code == 200
            
            # Step 5: User submits checkout form
            checkout_response = pixels_client.post(
                "/pixels/form_submitted",
                json=web_pixels_payloads["checkout_form"],
                headers=session_headers
            )
            assert checkout_response.status_code == 200
            
            # Verify all events were published to Redis
            assert mock_pixels_redis.publish_event.call_count == 4  # 3 pixels + 1 checkout form
            assert mock_webhook_redis.publish_event.call_count == 1  # 1 webhook
            
            # Verify event data correlation
            pixels_calls = mock_pixels_redis.publish_event.call_args_list
            webhook_calls = mock_webhook_redis.publish_event.call_args_list
            
            # Check session correlation across all events
            for call in pixels_calls:
                channel, event_data = call[0]
                assert event_data["session_id"] == session_id
                assert event_data["customer_id"] == customer_id
            
            for call in webhook_calls:
                channel, event_data = call[0]
                assert event_data["customer_id"] == customer_id
    
    @pytest.mark.asyncio
    async def test_session_correlation_processing(self):
        """Test event processor correlation of Web Pixels and webhook events"""
        
        processor = EventProcessor()
        session_id = "correlation_test_session"
        customer_id = "correlation_customer_123"
        
        # Simulate Web Pixels events
        dom_events = [
            {
                "event_type": "page_viewed",
                "source": "web_pixels",
                "session_id": session_id,
                "customer_id": customer_id,
                "data": {"url": "https://shop.com/products/test", "time_on_page": 30000},
                "timestamp": "2023-01-01T12:00:00Z"
            },
            {
                "event_type": "clicked",
                "source": "web_pixels",
                "session_id": session_id,
                "customer_id": customer_id,
                "data": {"clientX": 150, "clientY": 200, "element_tag": "button"},
                "timestamp": "2023-01-01T12:01:00Z"
            },
            {
                "event_type": "form_submitted",
                "source": "web_pixels",
                "session_id": session_id,
                "customer_id": customer_id,
                "data": {"form_id": "add-to-cart-form"},
                "timestamp": "2023-01-01T12:02:00Z"
            }
        ]
        
        # Simulate Shopify webhook events
        webhook_events = [
            {
                "event_type": "cart_create",
                "source": "shopify_webhook",
                "session_id": session_id,
                "customer_id": customer_id,
                "shop_domain": "test-shop.myshopify.com",
                "data": {"cart_id": "corr_cart_123", "total_price": "79.99"},
                "timestamp": "2023-01-01T12:02:30Z"
            },
            {
                "event_type": "checkout_create",
                "source": "shopify_webhook",
                "session_id": session_id,
                "customer_id": customer_id,
                "shop_domain": "test-shop.myshopify.com",
                "data": {"checkout_id": "corr_checkout_123", "total_price": "79.99"},
                "timestamp": "2023-01-01T12:05:00Z"
            },
            {
                "event_type": "order_create",
                "source": "shopify_webhook",
                "session_id": session_id,
                "customer_id": customer_id,
                "shop_domain": "test-shop.myshopify.com",
                "data": {"order_id": 999888, "total_price": "79.99"},
                "timestamp": "2023-01-01T12:06:00Z"
            }
        ]
        
        # Process all events
        for event in dom_events:
            await processor.process_event("dom_events", event)
        
        for event in webhook_events:
            await processor.process_event("cart_events", event)
        
        # Verify session correlation
        assert session_id in processor.sessions
        journey = processor.sessions[session_id]
        
        # Check event counts
        assert len(journey.dom_events) == 3
        assert len(journey.webhook_events) == 3
        assert len(journey.conversion_events) == 1  # order_create
        
        # Verify behavioral analysis
        engagement_score = journey.get_engagement_score()
        assert engagement_score > 0.5  # Should be high engagement
        
        # Check abandonment signals
        signals = journey.detect_abandonment_signals()
        assert signals["cart_without_checkout"] is False  # Has checkout and order
        
        # Verify processing statistics
        assert processor.processing_stats["dom_events"] == 3
        assert processor.processing_stats["webhook_events"] == 3
        assert processor.processing_stats["session_correlations"] >= 1
    
    @pytest.mark.asyncio
    async def test_abandonment_scenario(self):
        """Test cart abandonment detection across both data streams"""
        
        processor = EventProcessor()
        session_id = "abandonment_session"
        customer_id = "abandonment_customer"
        
        # User browses and shows interest
        engagement_events = [
            {
                "event_type": "page_viewed",
                "source": "web_pixels",
                "session_id": session_id,
                "customer_id": customer_id,
                "data": {"url": "https://shop.com/products/expensive-item", "time_on_page": 45000},
                "timestamp": "2023-01-01T12:00:00Z"
            }
        ]
        
        # Multiple rapid clicks indicating hesitation
        rapid_clicks = [
            {
                "event_type": "clicked",
                "source": "web_pixels",
                "session_id": session_id,
                "customer_id": customer_id,
                "data": {"clientX": 100 + i * 10, "clientY": 200 + i * 10, "element_tag": "button"},
                "timestamp": f"2023-01-01T12:0{i+1}:00Z"
            }
            for i in range(12)  # Rapid clicking pattern
        ]
        
        # Form abandonment
        form_events = [
            {
                "event_type": "input_focused",
                "source": "web_pixels",
                "session_id": session_id,
                "customer_id": customer_id,
                "data": {"element_type": "email", "form_id": "checkout"},
                "timestamp": "2023-01-01T12:15:00Z"
            },
            {
                "event_type": "input_changed",
                "source": "web_pixels",
                "session_id": session_id,
                "customer_id": customer_id,
                "data": {"element_type": "email", "element_value": "test@"},
                "timestamp": "2023-01-01T12:15:30Z"
            }
            # No form submission - abandonment
        ]
        
        # Cart creation but no checkout
        cart_event = {
            "event_type": "cart_create",
            "source": "shopify_webhook",
            "session_id": session_id,
            "customer_id": customer_id,
            "data": {"cart_id": "abandoned_cart_999", "total_price": "299.99"},
            "timestamp": "2023-01-01T12:16:00Z"
        }
        
        # Process all events
        all_events = engagement_events + rapid_clicks + form_events + [cart_event]
        
        for event in all_events:
            if event["source"] == "web_pixels":
                await processor.process_event("dom_events", event)
            else:
                await processor.process_event("cart_events", event)
        
        # Verify abandonment detection
        journey = processor.sessions[session_id]
        signals = journey.detect_abandonment_signals()
        
        assert signals["rapid_clicks"] is True
        assert signals["form_abandonment"] is True
        assert signals["cart_without_checkout"] is True
        
        # Verify no conversion occurred
        assert len(journey.conversion_events) == 0
        assert len(journey.webhook_events) == 1  # Just cart creation
    
    @pytest.mark.asyncio
    async def test_high_volume_concurrent_processing(self):
        """Test system under high-volume concurrent load"""
        
        processor = EventProcessor()
        
        # Simulate multiple concurrent user sessions
        num_concurrent_sessions = 20
        events_per_session = 15
        
        async def simulate_user_session(session_idx):
            session_id = f"concurrent_session_{session_idx}"
            customer_id = f"concurrent_customer_{session_idx}"
            
            # Mixed event types per session
            events = []
            
            # Page views
            events.append({
                "event_type": "page_viewed",
                "source": "web_pixels",
                "session_id": session_id,
                "customer_id": customer_id,
                "data": {"url": f"https://shop.com/products/item-{session_idx}"},
                "timestamp": "2023-01-01T12:00:00Z"
            })
            
            # Clicks and interactions
            for i in range(events_per_session - 3):
                events.append({
                    "event_type": "clicked",
                    "source": "web_pixels",
                    "session_id": session_id,
                    "customer_id": customer_id,
                    "data": {"clientX": i * 50, "clientY": i * 50, "element_tag": "button"},
                    "timestamp": f"2023-01-01T12:{i:02d}:00Z"
                })
            
            # Cart and order events
            events.append({
                "event_type": "cart_create",
                "source": "shopify_webhook",
                "session_id": session_id,
                "customer_id": customer_id,
                "data": {"cart_id": f"cart_{session_idx}", "total_price": f"{session_idx * 10}.99"},
                "timestamp": "2023-01-01T12:30:00Z"
            })
            
            events.append({
                "event_type": "order_create",
                "source": "shopify_webhook",
                "session_id": session_id,
                "customer_id": customer_id,
                "data": {"order_id": session_idx * 1000, "total_price": f"{session_idx * 10}.99"},
                "timestamp": "2023-01-01T12:35:00Z"
            })
            
            # Process events for this session
            for event in events:
                if event["source"] == "web_pixels":
                    await processor.process_event("dom_events", event)
                else:
                    await processor.process_event("webhook_events", event)
        
        # Run all sessions concurrently
        session_tasks = [simulate_user_session(i) for i in range(num_concurrent_sessions)]
        await asyncio.gather(*session_tasks)
        
        # Verify all sessions were processed
        assert len(processor.sessions) == num_concurrent_sessions
        
        # Verify statistics
        expected_total = num_concurrent_sessions * events_per_session
        assert processor.processing_stats["total_events"] >= expected_total
        
        # Verify each session has expected structure
        for session_idx in range(num_concurrent_sessions):
            session_id = f"concurrent_session_{session_idx}"
            assert session_id in processor.sessions
            
            journey = processor.sessions[session_id]
            assert len(journey.dom_events) >= 1  # At least page view + clicks
            assert len(journey.webhook_events) == 2  # Cart + order
            assert len(journey.conversion_events) == 1  # Order
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self):
        """Test system resilience to errors and invalid data"""
        
        processor = EventProcessor()
        session_id = "error_test_session"
        
        # Valid events
        valid_events = [
            {
                "event_type": "clicked",
                "source": "web_pixels",
                "session_id": session_id,
                "customer_id": "valid_customer",
                "data": {"clientX": 100, "clientY": 200, "element_tag": "button"},
                "timestamp": "2023-01-01T12:00:00Z"
            }
        ]
        
        # Invalid events (should be handled gracefully)
        invalid_events = [
            {
                # Missing required fields
                "event_type": "clicked",
                "source": "web_pixels",
                "session_id": session_id,
                # Missing data field
                "timestamp": "invalid_timestamp"
            },
            {
                # Invalid event type
                "event_type": "nonexistent_type",
                "source": "web_pixels", 
                "session_id": session_id,
                "data": {},
                "timestamp": "2023-01-01T12:00:00Z"
            }
        ]
        
        # Process valid events first
        for event in valid_events:
            await processor.process_event("dom_events", event)
        
        # Process invalid events - should not crash the system
        for event in invalid_events:
            try:
                await processor.process_event("dom_events", event)
            except Exception:
                pass  # Expected to fail, should not crash processor
        
        # Verify valid events were still processed
        assert session_id in processor.sessions
        journey = processor.sessions[session_id]
        assert len(journey.dom_events) >= 1
        
        # System should continue functioning
        post_error_event = {
            "event_type": "page_viewed",
            "source": "web_pixels",
            "session_id": session_id,
            "customer_id": "valid_customer",
            "data": {"url": "https://shop.com/recovery"},
            "timestamp": "2023-01-01T12:30:00Z"
        }
        
        await processor.process_event("dom_events", post_error_event)
        assert len(journey.dom_events) >= 2


@pytest.mark.asyncio 
async def test_performance_under_load():
    """Performance test for sustained high-volume processing"""
    
    processor = EventProcessor()
    
    start_time = time.time()
    
    # Process large number of events
    num_events = 1000
    batch_size = 50
    
    for batch in range(0, num_events, batch_size):
        batch_tasks = []
        
        for i in range(batch, min(batch + batch_size, num_events)):
            event = {
                "event_type": "clicked",
                "source": "web_pixels",
                "session_id": f"perf_session_{i % 100}",  # 100 sessions
                "customer_id": f"perf_customer_{i % 100}",
                "data": {"clientX": i % 1000, "clientY": i % 1000, "element_tag": "button"},
                "timestamp": "2023-01-01T12:00:00Z"
            }
            
            task = processor.process_event("click_events", event)
            batch_tasks.append(task)
        
        await asyncio.gather(*batch_tasks, return_exceptions=True)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    # Performance assertions
    assert processing_time < 30  # Should process 1000 events in under 30 seconds
    assert processor.processing_stats["total_events"] >= num_events
    
    events_per_second = num_events / processing_time
    assert events_per_second > 30  # Should handle at least 30 events/second
    
    print(f"Processed {num_events} events in {processing_time:.2f} seconds")
    print(f"Rate: {events_per_second:.1f} events/second")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])