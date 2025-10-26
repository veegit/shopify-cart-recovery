#!/usr/bin/env python3
"""
Quick test script to verify all services are running correctly
"""

import requests
import json
import time
from datetime import datetime

def test_service_health(name, url):
    """Test if a service health endpoint responds"""
    print(f"\n{'='*60}")
    print(f"Testing {name}")
    print(f"{'='*60}")

    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✓ {name} is healthy")
            print(f"  Response: {response.json()}")
            return True
        else:
            print(f"✗ {name} returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"✗ Cannot connect to {name} at {url}")
        print(f"  Make sure the service is running with: docker-compose up")
        return False
    except Exception as e:
        print(f"✗ Error testing {name}: {e}")
        return False


def test_webhook_endpoint():
    """Test sending a sample webhook event"""
    print(f"\n{'='*60}")
    print("Testing Webhook Handler - Cart Create Event")
    print(f"{'='*60}")

    url = "http://localhost:8101/webhooks/carts/create"

    # Sample cart webhook payload
    payload = {
        "id": 123456789,
        "token": "test_cart_token_abc123",
        "line_items": [
            {
                "id": 1,
                "product_id": 789,
                "variant_id": 101,
                "title": "Test Product",
                "quantity": 2,
                "price": "29.99"
            }
        ],
        "note": None,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }

    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Topic": "carts/create",
        "X-Shopify-Hmac-Sha256": "test_signature_for_development",
        "X-Shopify-Shop-Domain": "test-shop.myshopify.com"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code in [200, 201]:
            print("✓ Webhook received and processed successfully")
            print("\nCheck event processor logs to see the event:")
            print("  docker logs event-processor")
            return True
        else:
            print(f"⚠ Webhook returned status {response.status_code}")
            return False

    except Exception as e:
        print(f"✗ Error sending webhook: {e}")
        return False


def test_web_pixels_endpoint():
    """Test sending a sample Web Pixels event"""
    print(f"\n{'='*60}")
    print("Testing Web Pixels Handler - Click Event")
    print(f"{'='*60}")

    url = "http://localhost:8102/pixels/clicked"

    # Sample click event from Web Pixels
    payload = {
        "clientX": 150,
        "clientY": 250,
        "element": {
            "id": "add-to-cart-button",
            "tagName": "BUTTON",
            "className": "btn btn-primary add-to-cart",
            "href": None,
            "value": "Add to Cart"
        },
        "session_id": "test_session_" + str(int(time.time())),
        "customer_id": None,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    headers = {
        "Content-Type": "application/json",
        "Origin": "https://test-shop.myshopify.com"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code in [200, 201]:
            print("✓ Web Pixels event received and processed successfully")
            print("\nCheck event processor logs to see the event:")
            print("  docker logs event-processor")
            return True
        else:
            print(f"⚠ Web Pixels event returned status {response.status_code}")
            return False

    except Exception as e:
        print(f"✗ Error sending Web Pixels event: {e}")
        return False


def test_form_interaction():
    """Test form interaction event"""
    print(f"\n{'='*60}")
    print("Testing Web Pixels Handler - Form Input Event")
    print(f"{'='*60}")

    url = "http://localhost:8102/pixels/input_changed"

    payload = {
        "element": {
            "id": "email-input",
            "tagName": "INPUT",
            "className": "form-control",
            "value": "test@example.com"
        },
        "session_id": "test_session_" + str(int(time.time())),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    try:
        response = requests.post(url, json=payload, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code in [200, 201]:
            print("✓ Form input event processed successfully")
            return True
        else:
            print(f"⚠ Returned status {response.status_code}")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    print("\n" + "="*60)
    print("Shopify Cart Recovery - Service Test Suite")
    print("="*60)

    results = []

    # Test health endpoints
    results.append(test_service_health(
        "Webhook Handler",
        "http://localhost:8101/health"
    ))

    results.append(test_service_health(
        "Web Pixels Handler",
        "http://localhost:8102/health"
    ))

    # Test webhook functionality
    results.append(test_webhook_endpoint())

    # Test Web Pixels functionality
    results.append(test_web_pixels_endpoint())

    # Test form interaction
    results.append(test_form_interaction())

    # Summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("✓ All tests passed! Your services are working correctly.")
    else:
        print("⚠ Some tests failed. Check the output above for details.")
        print("\nTroubleshooting:")
        print("1. Make sure Docker services are running: docker-compose ps")
        print("2. Check logs: docker-compose logs")
        print("3. Restart services: docker-compose restart")

    print("\nNext Steps:")
    print("• View real-time logs: docker-compose logs -f")
    print("• Monitor event processor: docker logs -f event-processor")
    print("• Monitor Redis messages: docker exec -it shopify-cart-redis redis-cli MONITOR")
    print("• Run unit tests: docker-compose run --rm shopify-webhooks pytest")


if __name__ == "__main__":
    main()
