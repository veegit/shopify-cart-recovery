#!/usr/bin/env python3
"""
Helper script to generate valid HMAC-SHA256 signatures for webhook testing.
Use this when testing in production mode or when you need valid signatures.
"""

import hashlib
import hmac
import json
import sys


def generate_signature(payload_dict, secret):
    """
    Generate HMAC-SHA256 signature for a webhook payload.

    Args:
        payload_dict: Dictionary containing the webhook payload
        secret: Shopify webhook secret

    Returns:
        HMAC-SHA256 signature as hex string
    """
    # Convert payload to JSON string (as Shopify sends it)
    payload_json = json.dumps(payload_dict, separators=(',', ':'))
    payload_bytes = payload_json.encode('utf-8')

    # Generate HMAC signature
    signature = hmac.new(
        secret.encode('utf-8'),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()

    return signature


def generate_curl_command(endpoint, payload_dict, secret, shop_domain="test-shop.myshopify.com"):
    """
    Generate a complete curl command with valid HMAC signature.

    Args:
        endpoint: Webhook endpoint (e.g., "carts/create")
        payload_dict: Dictionary containing the webhook payload
        secret: Shopify webhook secret
        shop_domain: Shop domain for testing

    Returns:
        Complete curl command string
    """
    signature = generate_signature(payload_dict, secret)
    payload_json = json.dumps(payload_dict, indent=2)

    curl_command = f"""curl -X POST http://localhost:8101/webhooks/{endpoint} \\
  -H "Content-Type: application/json" \\
  -H "X-Shopify-Topic: {endpoint.replace('/', '/').replace('_', '/')}" \\
  -H "X-Shopify-Hmac-Sha256: {signature}" \\
  -H "X-Shopify-Shop-Domain: {shop_domain}" \\
  -H "X-Shopify-Timestamp: $(date +%s)" \\
  -d '{payload_json}'"""

    return curl_command


if __name__ == "__main__":
    # Example usage
    print("="*70)
    print("Shopify Webhook HMAC Signature Generator")
    print("="*70)
    print()

    # Sample cart webhook payload
    sample_cart = {
        "id": 123456789,
        "token": "cart_token_abc123",
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
        "created_at": "2025-10-26T10:00:00Z",
        "updated_at": "2025-10-26T10:00:00Z"
    }

    if len(sys.argv) > 1:
        secret = sys.argv[1]
    else:
        print("Usage: python generate_webhook_signature.py <webhook_secret>")
        print()
        print("For development mode (no signature needed):")
        print("-" * 70)
        print(generate_curl_command("carts/create", sample_cart, "not_used").replace(
            '-H "X-Shopify-Hmac-Sha256: .*"',
            '-H "X-Shopify-Hmac-Sha256: dev_mode_no_validation"'
        ))
        print()
        print("-" * 70)
        print()
        print("Note: In development mode (APP_ENV=development), signature")
        print("validation is disabled, so you can use any value or omit it.")
        print()
        sys.exit(0)

    print(f"Secret: {secret}")
    print()

    # Generate signature
    signature = generate_signature(sample_cart, secret)
    print(f"Generated Signature: {signature}")
    print()

    # Generate full curl command
    print("Complete curl command:")
    print("-" * 70)
    print(generate_curl_command("carts/create", sample_cart, secret))
    print("-" * 70)
    print()

    print("To test other endpoints, modify the payload and endpoint in this script.")
