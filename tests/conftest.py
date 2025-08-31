"""
Pytest configuration and shared fixtures for Shopify Cart Recovery tests.
Configures test environment and provides common test utilities.
"""

import pytest
import asyncio
import os
import sys
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, patch

# Add the project root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import test utilities
from tests.fixtures import (
    MockShopifyPayloads, MockWebPixelsPayloads, 
    UserJourneyGenerator, TestHelpers, LoadTestGenerator
)


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings():
    """Mock application settings for testing"""
    mock_settings = AsyncMock()
    mock_settings.redis.host = "localhost"
    mock_settings.redis.port = 6379
    mock_settings.redis.db = 15  # Use test database
    mock_settings.redis.password = None
    
    mock_settings.shopify.webhook_secret = "test_webhook_secret"
    mock_settings.shopify.api_key = "test_api_key"
    mock_settings.shopify.api_secret = "test_api_secret"
    mock_settings.shopify.app_url = "https://test-app.com"
    
    mock_settings.app.env = "test"
    mock_settings.app.port = 8000
    mock_settings.app.host = "0.0.0.0"
    
    mock_settings.logging.level = "DEBUG"
    mock_settings.logging.format = "json"
    
    mock_settings.web_pixels.endpoint = "https://test-app.com/pixels"
    
    return mock_settings


@pytest.fixture
async def mock_redis_client():
    """Mock Redis client for testing"""
    mock_client = AsyncMock()
    mock_client.health_check.return_value = True
    mock_client.publish_event.return_value = True
    mock_client.ping.return_value = b"PONG"
    
    # Mock Redis pub/sub functionality
    mock_pubsub = AsyncMock()
    mock_pubsub.subscribe.return_value = None
    mock_pubsub.listen.return_value = []
    mock_pubsub.unsubscribe.return_value = None
    mock_pubsub.close.return_value = None
    
    mock_client.pubsub.return_value = mock_pubsub
    
    return mock_client


@pytest.fixture
def test_session_data():
    """Provide test session data"""
    return {
        "session_id": "test_session_abc123",
        "customer_id": "test_customer_xyz789", 
        "shop_domain": "test-shop.myshopify.com"
    }


@pytest.fixture
def webhook_test_data():
    """Provide webhook test data with various payload types"""
    return {
        "cart_create": MockShopifyPayloads.cart_create(),
        "checkout_create": MockShopifyPayloads.checkout_create(),
        "order_create": MockShopifyPayloads.order_create(),
        "customer_create": MockShopifyPayloads.customer_create()
    }


@pytest.fixture
def pixels_test_data():
    """Provide Web Pixels test data with various event types"""
    return {
        "clicked": MockWebPixelsPayloads.clicked_event(),
        "input_changed": MockWebPixelsPayloads.input_changed_event(),
        "form_submitted": MockWebPixelsPayloads.form_submitted_event(),
        "page_viewed": MockWebPixelsPayloads.page_viewed_event()
    }


@pytest.fixture
def complete_user_journey():
    """Provide complete user journey for testing session correlation"""
    return UserJourneyGenerator.generate_complete_conversion_journey()


@pytest.fixture
def abandonment_journey():
    """Provide abandonment journey for testing abandonment detection"""
    return UserJourneyGenerator.generate_abandonment_journey()


@pytest.fixture
async def isolated_event_processor():
    """Provide isolated event processor for testing"""
    from apps.event_processor.main import EventProcessor
    
    processor = EventProcessor()
    yield processor
    
    # Cleanup
    processor.sessions.clear()
    processor.processing_stats = {
        "total_events": 0,
        "dom_events": 0,
        "webhook_events": 0,
        "session_correlations": 0,
        "insights_generated": 0
    }


@pytest.fixture
def performance_test_config():
    """Configuration for performance tests"""
    return {
        "concurrent_sessions": 50,
        "events_per_session": 25,
        "max_processing_time_seconds": 30,
        "min_events_per_second": 50
    }


class TestEnvironment:
    """Test environment manager"""
    
    def __init__(self):
        self.original_env = {}
    
    def set_test_env_vars(self):
        """Set environment variables for testing"""
        test_vars = {
            "REDIS_HOST": "localhost",
            "REDIS_PORT": "6379",
            "REDIS_DB": "15",
            "APP_ENV": "test",
            "LOG_LEVEL": "DEBUG",
            "SHOPIFY_WEBHOOK_SECRET": "test_webhook_secret",
            "SHOPIFY_API_KEY": "test_api_key",
            "SHOPIFY_API_SECRET": "test_api_secret"
        }
        
        for key, value in test_vars.items():
            self.original_env[key] = os.environ.get(key)
            os.environ[key] = value
    
    def restore_env_vars(self):
        """Restore original environment variables"""
        for key, original_value in self.original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


@pytest.fixture(scope="session", autouse=True)
def test_environment():
    """Set up test environment (runs once per test session)"""
    env = TestEnvironment()
    env.set_test_env_vars()
    
    yield env
    
    env.restore_env_vars()


@pytest.fixture(autouse=True)
def isolate_redis_operations():
    """Automatically mock Redis operations in all tests to prevent side effects"""
    with patch('apps.shared.redis_client.get_redis_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.health_check.return_value = True
        mock_client.publish_event.return_value = True
        mock_get_client.return_value = mock_client
        yield mock_client


@pytest.fixture
def capture_logs():
    """Capture log messages during tests"""
    import logging
    from io import StringIO
    
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    
    # Add handler to relevant loggers
    loggers = [
        logging.getLogger('webhook_handler'),
        logging.getLogger('web_pixels_handler'),
        logging.getLogger('event_processor'),
        logging.getLogger('redis_client')
    ]
    
    for logger in loggers:
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    
    yield log_capture
    
    # Cleanup
    for logger in loggers:
        logger.removeHandler(handler)


@pytest.fixture
async def async_test_timeout():
    """Provide timeout for async tests"""
    return 30  # 30 seconds timeout


# Custom pytest markers for better test organization
pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.timeout(60)  # Global timeout for all tests
]


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test file names"""
    for item in items:
        # Add markers based on test file names
        if "test_integration" in item.fspath.basename:
            item.add_marker(pytest.mark.integration)
        elif "performance" in item.name or "load" in item.name:
            item.add_marker(pytest.mark.performance)
        elif "test_" in item.fspath.basename and "integration" not in item.fspath.basename:
            item.add_marker(pytest.mark.unit)


def pytest_runtest_setup(item):
    """Setup for each test"""
    # Skip performance tests in regular test runs unless explicitly requested
    if item.get_closest_marker("performance"):
        if not item.config.getoption("--run-performance", default=False):
            pytest.skip("Performance tests skipped (use --run-performance to run)")


def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--run-performance",
        action="store_true",
        default=False,
        help="Run performance tests"
    )
    parser.addoption(
        "--run-integration",
        action="store_true", 
        default=False,
        help="Run integration tests"
    )


# Performance test utilities
class PerformanceAssertion:
    """Helper for performance assertions in tests"""
    
    @staticmethod
    def assert_processing_time(actual_time: float, max_time: float, operation: str):
        """Assert processing time is within acceptable limits"""
        assert actual_time <= max_time, (
            f"{operation} took {actual_time:.2f}s, "
            f"should be under {max_time}s"
        )
    
    @staticmethod
    def assert_throughput(events_processed: int, time_taken: float, min_rate: float):
        """Assert throughput meets minimum requirements"""
        actual_rate = events_processed / time_taken if time_taken > 0 else 0
        assert actual_rate >= min_rate, (
            f"Throughput was {actual_rate:.1f} events/sec, "
            f"should be at least {min_rate} events/sec"
        )


@pytest.fixture
def performance_assertion():
    """Provide performance assertion utilities"""
    return PerformanceAssertion()