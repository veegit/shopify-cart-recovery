"""
Test fixtures and utilities for Shopify Cart Recovery application tests.
Provides mock data, helper functions, and common test scenarios.
"""

import json
import hmac
import hashlib
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, MagicMock
import pytest


class MockShopifyPayloads:
    """Mock Shopify webhook payloads for testing"""
    
    @staticmethod
    def cart_create(
        cart_id: str = "mock_cart_123",
        customer_id: int = 555555,
        total_price: str = "99.99"
    ) -> Dict[str, Any]:
        return {
            "id": cart_id,
            "token": f"cart_token_{cart_id}",
            "line_items": [
                {
                    "id": 111111111,
                    "product_id": 222222,
                    "variant_id": 333333,
                    "title": "Mock Test Product",
                    "quantity": 1,
                    "price": total_price,
                    "sku": "MOCK-SKU-001"
                }
            ],
            "total_price": total_price,
            "total_weight": 250,
            "item_count": 1,
            "currency": "USD",
            "created_at": "2023-01-01T12:00:00Z",
            "updated_at": "2023-01-01T12:00:00Z",
            "customer": {
                "id": customer_id,
                "email": f"customer{customer_id}@test.com"
            }
        }
    
    @staticmethod
    def checkout_create(
        checkout_id: str = "mock_checkout_456",
        customer_id: int = 555555,
        total_price: str = "109.99"
    ) -> Dict[str, Any]:
        return {
            "id": checkout_id,
            "token": f"checkout_token_{checkout_id}",
            "line_items": [
                {
                    "id": 444444444,
                    "product_id": 222222,
                    "variant_id": 333333,
                    "title": "Mock Test Product",
                    "quantity": 1,
                    "price": "99.99",
                    "sku": "MOCK-SKU-001"
                }
            ],
            "total_price": total_price,
            "subtotal_price": "99.99",
            "total_tax": "10.00",
            "currency": "USD",
            "email": f"customer{customer_id}@test.com",
            "billing_address": {
                "first_name": "Mock",
                "last_name": "Customer",
                "address1": "123 Test St",
                "city": "Test City",
                "country": "United States",
                "zip": "12345"
            },
            "created_at": "2023-01-01T12:05:00Z",
            "customer": {
                "id": customer_id,
                "email": f"customer{customer_id}@test.com"
            }
        }
    
    @staticmethod
    def order_create(
        order_id: int = 987654,
        customer_id: int = 555555,
        total_price: str = "119.99"
    ) -> Dict[str, Any]:
        return {
            "id": order_id,
            "number": f"MOCK{order_id}",
            "line_items": [
                {
                    "id": 777777777,
                    "product_id": 222222,
                    "variant_id": 333333,
                    "title": "Mock Test Product",
                    "quantity": 1,
                    "price": "99.99",
                    "sku": "MOCK-SKU-001"
                }
            ],
            "total_price": total_price,
            "subtotal_price": "99.99",
            "total_tax": "10.00",
            "currency": "USD",
            "financial_status": "pending",
            "fulfillment_status": "unfulfilled",
            "email": f"customer{customer_id}@test.com",
            "created_at": "2023-01-01T12:10:00Z",
            "processed_at": "2023-01-01T12:10:00Z",
            "customer": {
                "id": customer_id,
                "email": f"customer{customer_id}@test.com"
            }
        }
    
    @staticmethod
    def customer_create(
        customer_id: int = 888888,
        email: str = "newcustomer@test.com"
    ) -> Dict[str, Any]:
        return {
            "id": customer_id,
            "email": email,
            "first_name": "New",
            "last_name": "Customer",
            "phone": "+1234567890",
            "accepts_marketing": True,
            "orders_count": 0,
            "total_spent": "0.00",
            "tags": "new,test",
            "created_at": "2023-01-01T10:00:00Z",
            "updated_at": "2023-01-01T10:00:00Z"
        }


class MockWebPixelsPayloads:
    """Mock Web Pixels event payloads for testing"""
    
    @staticmethod
    def clicked_event(
        x: int = 150,
        y: int = 250,
        element_tag: str = "button",
        element_id: str = "mock-button",
        url: str = "https://test-shop.myshopify.com/products/test"
    ) -> Dict[str, Any]:
        return {
            "clientX": x,
            "clientY": y,
            "element_id": element_id,
            "element_class": "btn btn-primary",
            "element_tag": element_tag,
            "element_text": "Mock Button",
            "target_selector": f"{element_tag}#{element_id}",
            "page_x": x,
            "page_y": y + 100,
            "url": url
        }
    
    @staticmethod
    def input_changed_event(
        element_type: str = "email",
        element_value: str = "test@example.com",
        form_id: str = "mock-form"
    ) -> Dict[str, Any]:
        return {
            "element_id": f"mock-{element_type}-input",
            "element_name": element_type,
            "element_type": element_type,
            "element_value": element_value,
            "previous_value": "",
            "element_selector": f"input#{element_type}-input",
            "form_id": form_id,
            "url": "https://test-shop.myshopify.com/pages/contact"
        }
    
    @staticmethod
    def form_submitted_event(
        form_id: str = "mock-checkout-form",
        field_count: int = 6,
        filled_fields: int = 5
    ) -> Dict[str, Any]:
        return {
            "form_id": form_id,
            "form_name": "checkout",
            "form_action": "/checkout",
            "form_method": "POST",
            "field_count": field_count,
            "filled_fields": filled_fields,
            "form_selector": f"form#{form_id}",
            "submission_method": "click",
            "url": "https://test-shop.myshopify.com/checkout"
        }
    
    @staticmethod
    def page_viewed_event(
        url: str = "https://test-shop.myshopify.com/products/test",
        time_on_page: int = 30000,
        scroll_depth: float = 0.8
    ) -> Dict[str, Any]:
        return {
            "page_title": "Mock Product Page",
            "referrer": "https://google.com",
            "page_type": "product",
            "viewport_width": 1920,
            "viewport_height": 1080,
            "screen_width": 1920,
            "screen_height": 1080,
            "scroll_depth": scroll_depth,
            "time_on_page": time_on_page,
            "url": url
        }


class UserJourneyGenerator:
    """Generate realistic user journey event sequences for testing"""
    
    @staticmethod
    def generate_complete_conversion_journey(
        session_id: str = "journey_session_123",
        customer_id: str = "journey_customer_456"
    ) -> List[Dict[str, Any]]:
        """Generate a complete user journey from page view to purchase"""
        
        events = []
        base_time = datetime.now()
        
        # 1. Page view
        events.append({
            "type": "web_pixels",
            "channel": "dom_events",
            "event": {
                "event_type": "page_viewed",
                "source": "web_pixels",
                "session_id": session_id,
                "customer_id": customer_id,
                "data": MockWebPixelsPayloads.page_viewed_event(),
                "timestamp": base_time.isoformat()
            }
        })
        
        # 2. Product clicks (browsing behavior)
        for i in range(3):
            click_time = base_time + timedelta(seconds=30 * (i + 1))
            events.append({
                "type": "web_pixels",
                "channel": "click_events",
                "event": {
                    "event_type": "clicked",
                    "source": "web_pixels",
                    "session_id": session_id,
                    "customer_id": customer_id,
                    "data": MockWebPixelsPayloads.clicked_event(
                        x=100 + i * 50,
                        y=200 + i * 30,
                        element_id=f"product-option-{i}"
                    ),
                    "timestamp": click_time.isoformat()
                }
            })
        
        # 3. Form interaction (add to cart)
        form_time = base_time + timedelta(minutes=2)
        events.append({
            "type": "web_pixels",
            "channel": "form_events",
            "event": {
                "event_type": "input_changed",
                "source": "web_pixels",
                "session_id": session_id,
                "customer_id": customer_id,
                "data": MockWebPixelsPayloads.input_changed_event(
                    element_type="number",
                    element_value="1",
                    form_id="add-to-cart-form"
                ),
                "timestamp": form_time.isoformat()
            }
        })
        
        # 4. Cart creation webhook
        cart_time = base_time + timedelta(minutes=2, seconds=30)
        events.append({
            "type": "webhook",
            "channel": "cart_events",
            "event": {
                "event_type": "cart_create",
                "source": "shopify_webhook",
                "session_id": session_id,
                "customer_id": customer_id,
                "shop_domain": "test-shop.myshopify.com",
                "data": MockShopifyPayloads.cart_create(
                    customer_id=int(customer_id.split('_')[-1])
                ),
                "timestamp": cart_time.isoformat()
            }
        })
        
        # 5. Checkout form submission
        checkout_form_time = base_time + timedelta(minutes=5)
        events.append({
            "type": "web_pixels",
            "channel": "form_events",
            "event": {
                "event_type": "form_submitted",
                "source": "web_pixels",
                "session_id": session_id,
                "customer_id": customer_id,
                "data": MockWebPixelsPayloads.form_submitted_event(),
                "timestamp": checkout_form_time.isoformat()
            }
        })
        
        # 6. Checkout creation webhook
        checkout_time = base_time + timedelta(minutes=5, seconds=30)
        events.append({
            "type": "webhook",
            "channel": "checkout_events",
            "event": {
                "event_type": "checkout_create",
                "source": "shopify_webhook",
                "session_id": session_id,
                "customer_id": customer_id,
                "shop_domain": "test-shop.myshopify.com",
                "data": MockShopifyPayloads.checkout_create(
                    customer_id=int(customer_id.split('_')[-1])
                ),
                "timestamp": checkout_time.isoformat()
            }
        })
        
        # 7. Order creation (conversion)
        order_time = base_time + timedelta(minutes=8)
        events.append({
            "type": "webhook",
            "channel": "order_events",
            "event": {
                "event_type": "order_create",
                "source": "shopify_webhook",
                "session_id": session_id,
                "customer_id": customer_id,
                "shop_domain": "test-shop.myshopify.com",
                "data": MockShopifyPayloads.order_create(
                    customer_id=int(customer_id.split('_')[-1])
                ),
                "timestamp": order_time.isoformat()
            }
        })
        
        return events
    
    @staticmethod
    def generate_abandonment_journey(
        session_id: str = "abandon_session_789",
        customer_id: str = "abandon_customer_101"
    ) -> List[Dict[str, Any]]:
        """Generate user journey that shows abandonment signals"""
        
        events = []
        base_time = datetime.now()
        
        # 1. Page view with long engagement
        events.append({
            "type": "web_pixels",
            "channel": "dom_events",
            "event": {
                "event_type": "page_viewed",
                "source": "web_pixels",
                "session_id": session_id,
                "customer_id": customer_id,
                "data": MockWebPixelsPayloads.page_viewed_event(
                    time_on_page=120000,  # 2 minutes - high engagement
                    scroll_depth=0.9
                ),
                "timestamp": base_time.isoformat()
            }
        })
        
        # 2. Rapid clicking pattern (hesitation)
        for i in range(15):  # Triggers rapid_clicks signal
            click_time = base_time + timedelta(seconds=5 + i * 2)
            events.append({
                "type": "web_pixels",
                "channel": "click_events",
                "event": {
                    "event_type": "clicked",
                    "source": "web_pixels",
                    "session_id": session_id,
                    "customer_id": customer_id,
                    "data": MockWebPixelsPayloads.clicked_event(
                        x=100 + (i % 5) * 20,  # Scattered clicking
                        y=200 + (i % 3) * 30,
                        element_id=f"hesitation-click-{i}"
                    ),
                    "timestamp": click_time.isoformat()
                }
            })
        
        # 3. Form abandonment (start filling but don't submit)
        form_events = [
            ("input_focused", "email"),
            ("input_changed", "email"), 
            ("input_focused", "phone"),
            ("input_changed", "phone"),
            ("input_focused", "address"),
            # No form submission - abandonment
        ]
        
        for i, (event_type, field) in enumerate(form_events):
            form_time = base_time + timedelta(minutes=3, seconds=i * 10)
            events.append({
                "type": "web_pixels",
                "channel": "form_events",
                "event": {
                    "event_type": event_type,
                    "source": "web_pixels",
                    "session_id": session_id,
                    "customer_id": customer_id,
                    "data": MockWebPixelsPayloads.input_changed_event(
                        element_type=field,
                        element_value="partial_input",
                        form_id="checkout-form"
                    ),
                    "timestamp": form_time.isoformat()
                }
            })
        
        # 4. Cart creation but no checkout
        cart_time = base_time + timedelta(minutes=2)
        events.append({
            "type": "webhook", 
            "channel": "cart_events",
            "event": {
                "event_type": "cart_create",
                "source": "shopify_webhook",
                "session_id": session_id,
                "customer_id": customer_id,
                "shop_domain": "test-shop.myshopify.com",
                "data": MockShopifyPayloads.cart_create(
                    customer_id=int(customer_id.split('_')[-1]),
                    total_price="299.99"  # High value abandoned cart
                ),
                "timestamp": cart_time.isoformat()
            }
        })
        
        # No checkout or order events - pure abandonment
        
        return events


class TestHelpers:
    """Helper functions for testing"""
    
    @staticmethod
    def generate_hmac_signature(payload: str, secret: str) -> str:
        """Generate valid HMAC signature for webhook testing"""
        return hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    @staticmethod
    def create_webhook_headers(
        shop_domain: str = "test-shop.myshopify.com",
        topic: str = "carts/create",
        payload: str = "",
        secret: str = "test_secret"
    ) -> Dict[str, str]:
        """Create valid webhook headers with HMAC"""
        return {
            "X-Shopify-Shop-Domain": shop_domain,
            "X-Shopify-Topic": topic,
            "X-Shopify-Hmac-Sha256": f"sha256={TestHelpers.generate_hmac_signature(payload, secret)}",
            "X-Shopify-Timestamp": str(int(time.time())),
            "Content-Type": "application/json"
        }
    
    @staticmethod
    def create_pixels_headers(
        session_id: str = "test_session_123",
        customer_id: str = "test_customer_456",
        shop_domain: str = "test-shop.myshopify.com"
    ) -> Dict[str, str]:
        """Create headers for Web Pixels requests"""
        return {
            "X-Session-ID": session_id,
            "X-Customer-ID": customer_id,
            "X-Shop-Domain": shop_domain,
            "Content-Type": "application/json"
        }
    
    @staticmethod
    def create_mock_redis_client() -> AsyncMock:
        """Create mock Redis client for testing"""
        mock_client = AsyncMock()
        mock_client.health_check.return_value = True
        mock_client.publish_event.return_value = True
        return mock_client
    
    @staticmethod
    async def wait_for_async_processing(delay: float = 0.1):
        """Wait for async processing to complete in tests"""
        await asyncio.sleep(delay)


class LoadTestGenerator:
    """Generate high-volume test scenarios for performance testing"""
    
    @staticmethod
    async def generate_concurrent_sessions(
        num_sessions: int = 100,
        events_per_session: int = 20
    ) -> List[List[Dict[str, Any]]]:
        """Generate multiple concurrent user sessions for load testing"""
        
        sessions = []
        
        for session_idx in range(num_sessions):
            session_id = f"load_test_session_{session_idx}"
            customer_id = f"load_test_customer_{session_idx}"
            
            # Randomize journey type
            if session_idx % 3 == 0:
                # Conversion journey
                journey = UserJourneyGenerator.generate_complete_conversion_journey(
                    session_id, customer_id
                )
            elif session_idx % 3 == 1:
                # Abandonment journey
                journey = UserJourneyGenerator.generate_abandonment_journey(
                    session_id, customer_id
                )
            else:
                # Custom high-volume journey
                journey = []
                base_time = datetime.now()
                
                for event_idx in range(events_per_session):
                    event_time = base_time + timedelta(seconds=event_idx * 5)
                    journey.append({
                        "type": "web_pixels",
                        "channel": "click_events",
                        "event": {
                            "event_type": "clicked",
                            "source": "web_pixels",
                            "session_id": session_id,
                            "customer_id": customer_id,
                            "data": MockWebPixelsPayloads.clicked_event(
                                x=event_idx * 10,
                                y=event_idx * 15,
                                element_id=f"load_test_element_{event_idx}"
                            ),
                            "timestamp": event_time.isoformat()
                        }
                    })
            
            sessions.append(journey)
        
        return sessions
    
    @staticmethod
    def generate_stress_test_events(
        duration_seconds: int = 60,
        events_per_second: int = 100
    ) -> List[Dict[str, Any]]:
        """Generate high-frequency events for stress testing"""
        
        events = []
        total_events = duration_seconds * events_per_second
        base_time = datetime.now()
        
        for i in range(total_events):
            event_time = base_time + timedelta(seconds=i / events_per_second)
            session_id = f"stress_session_{i % 50}"  # Distribute across 50 sessions
            
            events.append({
                "type": "web_pixels",
                "channel": "click_events",
                "event": {
                    "event_type": "clicked",
                    "source": "web_pixels",
                    "session_id": session_id,
                    "customer_id": f"stress_customer_{i % 50}",
                    "data": MockWebPixelsPayloads.clicked_event(
                        x=i % 1000,
                        y=(i * 2) % 1000,
                        element_id=f"stress_element_{i % 100}"
                    ),
                    "timestamp": event_time.isoformat()
                }
            })
        
        return events


# Pytest fixtures
@pytest.fixture
def mock_shopify_payloads():
    """Fixture providing mock Shopify payloads"""
    return MockShopifyPayloads()


@pytest.fixture
def mock_web_pixels_payloads():
    """Fixture providing mock Web Pixels payloads"""
    return MockWebPixelsPayloads()


@pytest.fixture
def user_journey_generator():
    """Fixture providing user journey generator"""
    return UserJourneyGenerator()


@pytest.fixture
def test_helpers():
    """Fixture providing test helper functions"""
    return TestHelpers()


@pytest.fixture
async def mock_redis_client():
    """Fixture providing mock Redis client"""
    return TestHelpers.create_mock_redis_client()


@pytest.fixture
def load_test_generator():
    """Fixture providing load test generator"""
    return LoadTestGenerator()


@pytest.fixture
def sample_session_data():
    """Fixture providing sample session data for testing"""
    return {
        "session_id": "test_session_12345",
        "customer_id": "test_customer_67890",
        "shop_domain": "test-shop.myshopify.com",
        "start_time": datetime.now(),
        "events_processed": 0
    }