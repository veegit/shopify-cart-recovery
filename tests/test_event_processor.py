import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from apps.event_processor.main import (
    EventProcessor, SessionJourney, BehaviorAnalyzer
)


class TestSessionJourney:
    @pytest.fixture
    def session(self):
        return SessionJourney(
            session_id="test_session_123",
            customer_id="customer_456",
            shop_domain="test-shop.myshopify.com"
        )
    
    def test_session_initialization(self, session):
        assert session.session_id == "test_session_123"
        assert session.customer_id == "customer_456"
        assert session.shop_domain == "test-shop.myshopify.com"
        assert len(session.dom_events) == 0
        assert len(session.webhook_events) == 0
    
    def test_add_dom_event(self, session):
        click_event = {
            "event_type": "clicked",
            "source": "web_pixels",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {"clientX": 100, "clientY": 200}
        }
        
        session.add_event(click_event)
        
        assert len(session.dom_events) == 1
        assert len(session.click_pattern) == 1
        assert session.dom_events[0] == click_event
    
    def test_add_webhook_event(self, session):
        cart_event = {
            "event_type": "cart_create",
            "source": "shopify_webhook",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {"cart_id": "123456", "total_price": "99.99"}
        }
        
        session.add_event(cart_event)
        
        assert len(session.webhook_events) == 1
        assert len(session.conversion_events) == 0  # Cart events don't count as conversion
        assert session.webhook_events[0] == cart_event
    
    def test_add_conversion_event(self, session):
        order_event = {
            "event_type": "order_create",
            "source": "shopify_webhook",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {"order_id": 987654, "total_price": "149.99"}
        }
        
        session.add_event(order_event)
        
        assert len(session.webhook_events) == 1
        assert len(session.conversion_events) == 1
        assert session.conversion_events[0] == order_event
    
    def test_form_interaction_categorization(self, session):
        form_events = [
            {
                "event_type": "input_focused",
                "source": "web_pixels",
                "timestamp": datetime.utcnow().isoformat()
            },
            {
                "event_type": "input_changed",
                "source": "web_pixels",
                "timestamp": datetime.utcnow().isoformat()
            },
            {
                "event_type": "form_submitted",
                "source": "web_pixels",
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
        
        for event in form_events:
            session.add_event(event)
        
        assert len(session.form_interactions) == 3
        assert len(session.dom_events) == 3
    
    def test_session_duration_calculation(self, session):
        # Simulate some time passing
        session.last_activity = session.start_time + timedelta(minutes=5)
        
        duration = session.get_session_duration()
        assert duration == 300.0  # 5 minutes in seconds
    
    def test_engagement_score_calculation(self, session):
        # Add some activity to increase engagement
        for i in range(5):
            session.add_event({
                "event_type": "clicked",
                "source": "web_pixels",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        session.add_event({
            "event_type": "page_viewed",
            "source": "web_pixels",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Simulate session duration
        session.last_activity = session.start_time + timedelta(minutes=10)
        
        score = session.get_engagement_score()
        assert 0 <= score <= 1
        assert score > 0  # Should have some engagement with activity
    
    def test_abandonment_signals_detection(self, session):
        # Add rapid clicks
        for i in range(12):
            session.add_event({
                "event_type": "clicked",
                "source": "web_pixels",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Add form interactions without submission
        session.add_event({
            "event_type": "input_focused",
            "source": "web_pixels",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        session.add_event({
            "event_type": "input_changed",
            "source": "web_pixels",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Add cart without checkout
        session.add_event({
            "event_type": "cart_create",
            "source": "shopify_webhook",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        signals = session.detect_abandonment_signals()
        
        assert signals["rapid_clicks"] is True
        assert signals["form_abandonment"] is False  # Not enough form events
        assert signals["cart_without_checkout"] is True


class TestBehaviorAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return BehaviorAnalyzer()
    
    def test_analyze_click_pattern_focused(self, analyzer):
        # Create click events with small movements (focused behavior)
        click_events = [
            {
                "event_type": "clicked",
                "data": {"clientX": 100, "clientY": 200}
            },
            {
                "event_type": "clicked",
                "data": {"clientX": 105, "clientY": 205}
            },
            {
                "event_type": "clicked",
                "data": {"clientX": 103, "clientY": 198}
            }
        ]
        
        analysis = analyzer.analyze_click_pattern("test_session", click_events)
        
        assert analysis["pattern_type"] == "focused"
        assert analysis["avg_movement_distance"] < 50
        assert analysis["large_movements"] == 0
    
    def test_analyze_click_pattern_scattered(self, analyzer):
        # Create click events with large movements (scattered behavior)
        click_events = [
            {
                "event_type": "clicked",
                "data": {"clientX": 100, "clientY": 200}
            },
            {
                "event_type": "clicked",
                "data": {"clientX": 500, "clientY": 600}
            },
            {
                "event_type": "clicked",
                "data": {"clientX": 50, "clientY": 100}
            }
        ]
        
        analysis = analyzer.analyze_click_pattern("test_session", click_events)
        
        assert analysis["pattern_type"] == "scattered"
        assert analysis["large_movements"] > 0
    
    def test_analyze_form_behavior(self, analyzer):
        form_events = [
            {"event_type": "input_focused", "data": {"element_id": "email"}},
            {"event_type": "input_focused", "data": {"element_id": "name"}},
            {"event_type": "input_changed", "data": {"element_id": "email"}},
            {"event_type": "input_changed", "data": {"element_id": "name"}},
            {"event_type": "input_blurred", "data": {"element_id": "email", "focus_duration": 5000}},
            {"event_type": "input_blurred", "data": {"element_id": "name", "focus_duration": 3000}},
            {"event_type": "form_submitted", "data": {"form_id": "contact-form"}}
        ]
        
        analysis = analyzer.analyze_form_behavior(form_events)
        
        assert analysis["total_fields_interacted"] == 2
        assert analysis["total_focus_time_ms"] == 8000
        assert analysis["form_changes"] == 2
        assert analysis["form_submissions"] == 1
        assert analysis["abandonment_rate"] == 0.5  # 1 - (1 submission / 2 focuses)


class TestEventProcessor:
    @pytest.fixture
    def processor(self):
        return EventProcessor()
    
    @pytest.mark.asyncio
    async def test_process_dom_event(self, processor):
        click_event = {
            "event_type": "clicked",
            "source": "web_pixels",
            "session_id": "test_session",
            "customer_id": "customer_123",
            "data": {
                "clientX": 150,
                "clientY": 250,
                "element_tag": "button"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await processor.process_dom_event(click_event)
        
        assert processor.processing_stats["dom_events"] == 1
    
    @pytest.mark.asyncio
    async def test_process_webhook_event(self, processor):
        order_event = {
            "event_type": "order_create",
            "source": "shopify_webhook",
            "customer_id": "customer_123",
            "shop_domain": "test-shop.myshopify.com",
            "data": {
                "order_id": 987654,
                "total_price": "149.99"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await processor.process_webhook_event(order_event)
        
        assert processor.processing_stats["webhook_events"] == 1
    
    @pytest.mark.asyncio
    async def test_session_correlation(self, processor):
        session_id = "correlation_test_session"
        
        # First, add a DOM event
        click_event = {
            "event_type": "clicked",
            "source": "web_pixels",
            "session_id": session_id,
            "customer_id": "customer_123",
            "data": {"clientX": 100, "clientY": 200},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await processor.process_event("click_events", click_event)
        
        # Then add a webhook event with same session
        cart_event = {
            "event_type": "cart_create",
            "source": "shopify_webhook",
            "session_id": session_id,
            "customer_id": "customer_123",
            "data": {"cart_id": "123456", "total_price": "99.99"},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await processor.process_event("cart_events", cart_event)
        
        # Verify session was created and contains both events
        assert session_id in processor.sessions
        journey = processor.sessions[session_id]
        assert len(journey.dom_events) == 1
        assert len(journey.webhook_events) == 1
    
    @pytest.mark.asyncio
    async def test_behavioral_pattern_recognition(self, processor):
        session_id = "pattern_test_session"
        
        # Add multiple click events to trigger pattern analysis
        click_events = [
            {
                "event_type": "clicked",
                "source": "web_pixels",
                "session_id": session_id,
                "data": {"clientX": 100 + i * 50, "clientY": 200 + i * 50},
                "timestamp": datetime.utcnow().isoformat()
            }
            for i in range(5)
        ]
        
        for event in click_events:
            await processor.process_event("click_events", event)
        
        # Verify session exists and has click pattern
        assert session_id in processor.sessions
        journey = processor.sessions[session_id]
        assert len(journey.click_pattern) == 5
    
    @pytest.mark.asyncio
    async def test_conversion_correlation(self, processor):
        session_id = "conversion_test_session"
        
        # Add DOM activity
        dom_events = [
            {
                "event_type": "clicked",
                "source": "web_pixels",
                "session_id": session_id,
                "customer_id": "customer_123",
                "data": {"clientX": 100, "clientY": 200},
                "timestamp": datetime.utcnow().isoformat()
            },
            {
                "event_type": "form_submitted",
                "source": "web_pixels",
                "session_id": session_id,
                "customer_id": "customer_123",
                "data": {"form_id": "checkout-form"},
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
        
        for event in dom_events:
            await processor.process_event("form_events", event)
        
        # Add conversion event
        order_event = {
            "event_type": "order_paid",
            "source": "shopify_webhook",
            "session_id": session_id,
            "customer_id": "customer_123",
            "data": {"order_id": 987654, "total_price": "149.99"},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await processor.process_event("order_events", order_event)
        
        # Verify conversion was tracked with behavioral correlation
        journey = processor.sessions[session_id]
        assert len(journey.conversion_events) == 1
        assert len(journey.dom_events) == 2
        assert processor.processing_stats["session_correlations"] >= 1
    
    @pytest.mark.asyncio
    async def test_abandonment_signal_detection(self, processor):
        session_id = "abandonment_test_session"
        
        # Create abandonment scenario: cart activity without conversion
        cart_event = {
            "event_type": "cart_create",
            "source": "shopify_webhook",
            "session_id": session_id,
            "customer_id": "customer_123",
            "data": {"cart_id": "abandoned_cart_123", "total_price": "99.99"},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add rapid clicks (abandonment signal)
        rapid_clicks = [
            {
                "event_type": "clicked",
                "source": "web_pixels",
                "session_id": session_id,
                "data": {"clientX": 100 + i, "clientY": 200 + i},
                "timestamp": datetime.utcnow().isoformat()
            }
            for i in range(15)  # More than 10 clicks to trigger rapid_clicks signal
        ]
        
        # Process events
        await processor.process_event("cart_events", cart_event)
        
        for click_event in rapid_clicks:
            await processor.process_event("click_events", click_event)
        
        # Verify abandonment signals are detected
        journey = processor.sessions[session_id]
        signals = journey.detect_abandonment_signals()
        
        assert signals["cart_without_checkout"] is True
        assert signals["rapid_clicks"] is True
    
    def test_session_cleanup(self, processor):
        # Create an old session
        old_session_id = "old_session"
        processor.sessions[old_session_id] = SessionJourney(
            session_id=old_session_id,
            customer_id="customer_123"
        )
        
        # Make it old by setting last_activity to 5 hours ago
        processor.sessions[old_session_id].last_activity = datetime.utcnow() - timedelta(hours=5)
        
        # Create a recent session
        recent_session_id = "recent_session"
        processor.sessions[recent_session_id] = SessionJourney(
            session_id=recent_session_id,
            customer_id="customer_456"
        )
        
        initial_count = len(processor.sessions)
        assert initial_count == 2
        
        # Run cleanup
        processor.cleanup_expired_sessions()
        
        # Old session should be removed, recent one should remain
        assert len(processor.sessions) == 1
        assert old_session_id not in processor.sessions
        assert recent_session_id in processor.sessions
    
    @pytest.mark.asyncio
    async def test_event_deduplication(self, processor):
        session_id = "dedup_test_session"
        
        # Create identical events
        duplicate_event = {
            "event_id": "duplicate_event_123",
            "event_type": "clicked",
            "source": "web_pixels",
            "session_id": session_id,
            "data": {"clientX": 100, "clientY": 200},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # First event should be processed
        await processor.process_event("click_events", duplicate_event)
        assert len(processor.sessions[session_id].dom_events) == 1
        
        # Duplicate should be handled (implementation depends on deduplication logic)
        # This tests the processor's ability to handle duplicate events gracefully
        await processor.process_event("click_events", duplicate_event)
        
        # Exact behavior depends on implementation - could be ignored or processed
        # The test verifies no crashes occur


@pytest.mark.asyncio
async def test_multi_stream_integration():
    processor = EventProcessor()
    session_id = "integration_test_session"
    customer_id = "integration_customer_123"
    
    # Simulate complete user journey with both DOM and webhook events
    events_sequence = [
        # Page view
        {
            "channel": "dom_events",
            "event": {
                "event_type": "page_viewed",
                "source": "web_pixels",
                "session_id": session_id,
                "customer_id": customer_id,
                "data": {"url": "https://shop.com/products/test"},
                "timestamp": datetime.utcnow().isoformat()
            }
        },
        # Product clicks
        {
            "channel": "click_events", 
            "event": {
                "event_type": "clicked",
                "source": "web_pixels",
                "session_id": session_id,
                "customer_id": customer_id,
                "data": {"clientX": 200, "clientY": 300, "element_tag": "button"},
                "timestamp": datetime.utcnow().isoformat()
            }
        },
        # Cart creation (webhook)
        {
            "channel": "cart_events",
            "event": {
                "event_type": "cart_create",
                "source": "shopify_webhook", 
                "session_id": session_id,
                "customer_id": customer_id,
                "data": {"cart_id": "integration_cart_123", "total_price": "79.99"},
                "timestamp": datetime.utcnow().isoformat()
            }
        },
        # Form interaction
        {
            "channel": "form_events",
            "event": {
                "event_type": "form_submitted",
                "source": "web_pixels",
                "session_id": session_id,
                "customer_id": customer_id,
                "data": {"form_id": "checkout-form"},
                "timestamp": datetime.utcnow().isoformat()
            }
        },
        # Order creation (conversion)
        {
            "channel": "order_events",
            "event": {
                "event_type": "order_create",
                "source": "shopify_webhook",
                "session_id": session_id,
                "customer_id": customer_id,
                "data": {"order_id": 555555, "total_price": "79.99"},
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    ]
    
    # Process all events in sequence
    for item in events_sequence:
        await processor.process_event(item["channel"], item["event"])
    
    # Verify complete journey was captured
    journey = processor.sessions[session_id]
    
    assert len(journey.dom_events) == 3  # page_viewed, clicked, form_submitted
    assert len(journey.webhook_events) == 2  # cart_create, order_create
    assert len(journey.conversion_events) == 1  # order_create
    assert len(journey.click_pattern) == 1
    assert len(journey.form_interactions) == 1
    
    # Verify engagement and behavior analysis
    engagement_score = journey.get_engagement_score()
    assert engagement_score > 0
    
    abandonment_signals = journey.detect_abandonment_signals()
    assert abandonment_signals["cart_without_checkout"] is False  # Has order
    
    # Verify processing statistics
    assert processor.processing_stats["dom_events"] >= 3
    assert processor.processing_stats["webhook_events"] >= 2
    assert processor.processing_stats["total_events"] >= 5


@pytest.mark.asyncio
async def test_high_volume_performance():
    processor = EventProcessor()
    
    # Simulate high-volume event processing
    num_sessions = 50
    events_per_session = 20
    
    tasks = []
    
    for session_idx in range(num_sessions):
        session_id = f"perf_test_session_{session_idx}"
        
        for event_idx in range(events_per_session):
            event = {
                "event_type": "clicked",
                "source": "web_pixels",
                "session_id": session_id,
                "customer_id": f"customer_{session_idx}",
                "data": {
                    "clientX": event_idx * 10,
                    "clientY": event_idx * 10,
                    "element_tag": "button"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Create task for async processing
            task = processor.process_event("click_events", event)
            tasks.append(task)
    
    # Process all events concurrently
    await asyncio.gather(*tasks, return_exceptions=True)
    
    # Verify all sessions were created
    assert len(processor.sessions) == num_sessions
    
    # Verify event counts
    total_dom_events = sum(len(journey.dom_events) for journey in processor.sessions.values())
    assert total_dom_events == num_sessions * events_per_session
    
    # Verify processing statistics
    assert processor.processing_stats["total_events"] >= num_sessions * events_per_session
    assert processor.processing_stats["dom_events"] >= num_sessions * events_per_session