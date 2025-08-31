# Shopify Webhook Integration Examples

Complete examples for setting up and processing Shopify webhooks in the cart recovery system.

## 📡 Webhook Event Examples

### Cart Events

#### Cart Create Event
```json
{
  "id": "c1-1234567890",
  "token": "1234567890abcdef",
  "line_items": [
    {
      "id": 111111111,
      "product_id": 222222,
      "variant_id": 333333,
      "title": "Premium Running Shoes",
      "quantity": 1,
      "price": "129.99",
      "sku": "SHOES-RUN-001",
      "grams": 800,
      "vendor": "Athletic Brand",
      "product_type": "Footwear",
      "gift_card": false,
      "taxable": true,
      "requires_shipping": true
    }
  ],
  "total_price": "129.99",
  "subtotal_price": "129.99",
  "total_weight": 800,
  "item_count": 1,
  "currency": "USD",
  "created_at": "2023-01-15T10:30:00Z",
  "updated_at": "2023-01-15T10:30:00Z",
  "customer": {
    "id": 555555,
    "email": "customer@example.com",
    "accepts_marketing": true,
    "first_name": "John",
    "last_name": "Smith",
    "orders_count": 3,
    "total_spent": "456.78"
  },
  "note": null,
  "attributes": {}
}
```

#### Cart Update Event
```json
{
  "id": "c1-1234567890",
  "token": "1234567890abcdef",
  "line_items": [
    {
      "id": 111111111,
      "product_id": 222222,
      "variant_id": 333333,
      "title": "Premium Running Shoes",
      "quantity": 2,
      "price": "129.99",
      "sku": "SHOES-RUN-001"
    },
    {
      "id": 111111112,
      "product_id": 222223,
      "variant_id": 333334,
      "title": "Athletic Socks",
      "quantity": 3,
      "price": "15.99",
      "sku": "SOCKS-ATH-001"
    }
  ],
  "total_price": "307.95",
  "subtotal_price": "307.95",
  "item_count": 5,
  "updated_at": "2023-01-15T10:45:00Z"
}
```

### Checkout Events

#### Checkout Create Event
```json
{
  "id": 987654321,
  "token": "abcdef1234567890",
  "cart_token": "1234567890abcdef",
  "email": "customer@example.com",
  "gateway": "shopify_payments",
  "buyer_accepts_marketing": false,
  "created_at": "2023-01-15T11:00:00Z",
  "updated_at": "2023-01-15T11:00:00Z",
  "landing_site": "/products/premium-running-shoes",
  "referring_site": "https://www.google.com/",
  "line_items": [
    {
      "id": 111111111,
      "product_id": 222222,
      "variant_id": 333333,
      "title": "Premium Running Shoes",
      "quantity": 2,
      "price": "129.99",
      "sku": "SHOES-RUN-001"
    }
  ],
  "subtotal_price": "259.98",
  "total_tax": "20.80",
  "total_price": "280.78",
  "currency": "USD",
  "total_discounts": "0.00",
  "customer": {
    "id": 555555,
    "email": "customer@example.com",
    "first_name": "John",
    "last_name": "Smith"
  },
  "shipping_address": {
    "first_name": "John",
    "last_name": "Smith",
    "address1": "123 Main Street",
    "address2": "Apt 4B",
    "city": "New York",
    "province": "NY",
    "country": "United States",
    "zip": "10001",
    "phone": "+1-555-123-4567"
  },
  "billing_address": {
    "first_name": "John",
    "last_name": "Smith",
    "address1": "123 Main Street",
    "city": "New York",
    "province": "NY",
    "country": "United States",
    "zip": "10001"
  },
  "shipping_lines": [
    {
      "id": "shopify-Standard%20Shipping-5.00",
      "title": "Standard Shipping",
      "price": "5.00",
      "code": "Standard Shipping"
    }
  ],
  "payment_gateway_names": ["shopify_payments"],
  "processing_method": "checkout",
  "source_name": "web"
}
```

### Order Events

#### Order Create Event
```json
{
  "id": 123456789,
  "email": "customer@example.com",
  "closed_at": null,
  "created_at": "2023-01-15T11:15:00Z",
  "updated_at": "2023-01-15T11:15:00Z",
  "number": 1001,
  "note": null,
  "token": "order_token_123",
  "gateway": "shopify_payments",
  "test": false,
  "total_price": "280.78",
  "subtotal_price": "259.98",
  "total_weight": 1600,
  "total_tax": "20.80",
  "taxes_included": false,
  "currency": "USD",
  "financial_status": "pending",
  "confirmed": true,
  "total_discounts": "0.00",
  "buyer_accepts_marketing": false,
  "name": "#1001",
  "referring_site": "https://www.google.com/",
  "landing_site": "/products/premium-running-shoes",
  "cancelled_at": null,
  "cancel_reason": null,
  "user_id": 999999,
  "location_id": 888888,
  "source_identifier": "web",
  "source_url": null,
  "processed_at": "2023-01-15T11:15:00Z",
  "device_id": null,
  "phone": "+1-555-123-4567",
  "customer_locale": "en",
  "app_id": 580111,
  "browser_ip": "192.168.1.100",
  "checkout_id": 987654321,
  "checkout_token": "abcdef1234567890",
  "customer": {
    "id": 555555,
    "email": "customer@example.com",
    "accepts_marketing": true,
    "created_at": "2022-05-10T08:00:00Z",
    "updated_at": "2023-01-15T11:15:00Z",
    "first_name": "John",
    "last_name": "Smith",
    "orders_count": 4,
    "state": "enabled",
    "total_spent": "737.56",
    "last_order_id": 123456789,
    "note": "VIP Customer",
    "verified_email": true,
    "multipass_identifier": null,
    "tax_exempt": false,
    "phone": "+1-555-123-4567",
    "tags": "vip,repeat_customer",
    "last_order_name": "#1001",
    "currency": "USD",
    "marketing_opt_in_level": "confirmed_opt_in"
  },
  "discount_codes": [],
  "fulfillments": [],
  "fulfillment_status": null,
  "line_items": [
    {
      "id": 111111113,
      "variant_id": 333333,
      "title": "Premium Running Shoes",
      "quantity": 2,
      "sku": "SHOES-RUN-001",
      "variant_title": "Size 10 / Black",
      "vendor": "Athletic Brand",
      "fulfillment_service": "manual",
      "product_id": 222222,
      "requires_shipping": true,
      "taxable": true,
      "gift_card": false,
      "name": "Premium Running Shoes - Size 10 / Black",
      "variant_inventory_management": "shopify",
      "properties": [],
      "product_exists": true,
      "fulfillable_quantity": 2,
      "grams": 800,
      "price": "129.99",
      "total_discount": "0.00",
      "fulfillment_status": null,
      "price_set": {
        "shop_money": {
          "amount": "129.99",
          "currency_code": "USD"
        },
        "presentment_money": {
          "amount": "129.99",
          "currency_code": "USD"
        }
      }
    }
  ],
  "payment_gateway_names": ["shopify_payments"],
  "processing_method": "checkout",
  "shipping_address": {
    "first_name": "John",
    "address1": "123 Main Street",
    "phone": "+1-555-123-4567",
    "city": "New York",
    "zip": "10001",
    "province": "NY",
    "country": "United States",
    "last_name": "Smith",
    "address2": "Apt 4B",
    "company": null,
    "latitude": 40.7128,
    "longitude": -74.0060,
    "name": "John Smith",
    "country_code": "US",
    "province_code": "NY"
  },
  "shipping_lines": [
    {
      "id": 888888888,
      "title": "Standard Shipping",
      "price": "5.00",
      "code": "Standard Shipping",
      "source": "shopify",
      "phone": null,
      "requested_fulfillment_service_id": null,
      "delivery_category": null,
      "carrier_identifier": "usps",
      "discounted_price": "5.00",
      "price_set": {
        "shop_money": {
          "amount": "5.00",
          "currency_code": "USD"
        }
      }
    }
  ]
}
```

#### Order Paid Event
```json
{
  "id": 123456789,
  "number": 1001,
  "financial_status": "paid",
  "total_price": "280.78",
  "gateway": "shopify_payments",
  "payment_gateway_names": ["shopify_payments"],
  "processed_at": "2023-01-15T11:16:00Z",
  "transactions": [
    {
      "id": 777777777,
      "order_id": 123456789,
      "kind": "sale",
      "gateway": "shopify_payments",
      "status": "success",
      "message": "Transaction approved",
      "created_at": "2023-01-15T11:16:00Z",
      "test": false,
      "authorization": "auth123456",
      "location_id": 888888,
      "source_name": "web",
      "currency": "USD",
      "amount": "280.78",
      "device_id": null,
      "parent_id": null,
      "receipt": {
        "gift_card_id": null,
        "gift_card_last_characters": null
      }
    }
  ]
}
```

### Customer Events

#### Customer Create Event
```json
{
  "id": 555556,
  "email": "newcustomer@example.com",
  "accepts_marketing": true,
  "created_at": "2023-01-15T12:00:00Z",
  "updated_at": "2023-01-15T12:00:00Z",
  "first_name": "Jane",
  "last_name": "Doe",
  "orders_count": 0,
  "state": "enabled",
  "total_spent": "0.00",
  "last_order_id": null,
  "note": "Signed up via newsletter",
  "verified_email": true,
  "multipass_identifier": null,
  "tax_exempt": false,
  "phone": "+1-555-987-6543",
  "tags": "newsletter_subscriber,new_customer",
  "last_order_name": null,
  "currency": "USD",
  "addresses": [
    {
      "id": 777777777,
      "customer_id": 555556,
      "first_name": "Jane",
      "last_name": "Doe",
      "company": null,
      "address1": "456 Oak Avenue",
      "address2": null,
      "city": "Los Angeles",
      "province": "CA",
      "country": "United States",
      "zip": "90210",
      "phone": "+1-555-987-6543",
      "name": "Jane Doe",
      "province_code": "CA",
      "country_code": "US",
      "country_name": "United States",
      "default": true
    }
  ],
  "accepts_marketing_updated_at": "2023-01-15T12:00:00Z",
  "marketing_opt_in_level": "confirmed_opt_in",
  "sms_marketing_consent": null,
  "admin_graphql_api_id": "gid://shopify/Customer/555556"
}
```

## 🔒 Webhook Validation Examples

### HMAC Verification Implementation

```python
# webhook_validator.py
import hashlib
import hmac
import time
from typing import Optional

class WebhookValidator:
    def __init__(self, webhook_secret: str):
        self.webhook_secret = webhook_secret
        self.max_timestamp_age = 300  # 5 minutes
    
    def validate_hmac(self, payload: bytes, signature: str) -> bool:
        """Validate HMAC signature for webhook authenticity"""
        if not signature:
            return False
        
        # Remove 'sha256=' prefix if present
        if signature.startswith('sha256='):
            signature = signature[7:]
        
        # Calculate expected signature
        expected_signature = hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_signature, signature)
    
    def validate_timestamp(self, timestamp_str: Optional[str]) -> bool:
        """Validate webhook timestamp to prevent replay attacks"""
        if not timestamp_str:
            return False
        
        try:
            webhook_time = int(timestamp_str)
            current_time = int(time.time())
            
            # Check if webhook is not too old
            return abs(current_time - webhook_time) <= self.max_timestamp_age
        except (ValueError, TypeError):
            return False
    
    def validate_webhook(self, payload: bytes, headers: dict) -> tuple[bool, str]:
        """Complete webhook validation"""
        hmac_header = headers.get('X-Shopify-Hmac-Sha256')
        timestamp_header = headers.get('X-Shopify-Timestamp')
        shop_domain = headers.get('X-Shopify-Shop-Domain')
        topic = headers.get('X-Shopify-Topic')
        
        # Check required headers
        if not all([hmac_header, timestamp_header, shop_domain, topic]):
            return False, "Missing required headers"
        
        # Validate HMAC
        if not self.validate_hmac(payload, hmac_header):
            return False, "Invalid HMAC signature"
        
        # Validate timestamp
        if not self.validate_timestamp(timestamp_header):
            return False, "Invalid or expired timestamp"
        
        return True, "Valid webhook"

# Usage example
def process_webhook(request):
    validator = WebhookValidator(os.getenv('SHOPIFY_WEBHOOK_SECRET'))
    
    payload = request.body
    headers = {
        'X-Shopify-Hmac-Sha256': request.headers.get('X-Shopify-Hmac-Sha256'),
        'X-Shopify-Timestamp': request.headers.get('X-Shopify-Timestamp'),
        'X-Shopify-Shop-Domain': request.headers.get('X-Shopify-Shop-Domain'),
        'X-Shopify-Topic': request.headers.get('X-Shopify-Topic')
    }
    
    is_valid, message = validator.validate_webhook(payload, headers)
    
    if not is_valid:
        return {'error': message}, 401
    
    # Process valid webhook
    return process_valid_webhook(payload, headers)
```

### FastAPI Webhook Endpoint Implementation

```python
# webhook_endpoints.py
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
import json
import asyncio
from typing import Optional

app = FastAPI()

@app.post("/webhooks/carts/create")
async def handle_cart_create(
    request: Request,
    x_shopify_hmac_sha256: str = Header(...),
    x_shopify_timestamp: str = Header(...),
    x_shopify_shop_domain: str = Header(...),
    x_shopify_topic: str = Header(...)
):
    """Handle cart creation webhooks"""
    
    # Get raw payload
    payload = await request.body()
    
    # Validate webhook
    validator = WebhookValidator(settings.shopify.webhook_secret)
    headers = {
        'X-Shopify-Hmac-Sha256': x_shopify_hmac_sha256,
        'X-Shopify-Timestamp': x_shopify_timestamp,
        'X-Shopify-Shop-Domain': x_shopify_shop_domain,
        'X-Shopify-Topic': x_shopify_topic
    }
    
    is_valid, error_message = validator.validate_webhook(payload, headers)
    if not is_valid:
        raise HTTPException(status_code=401, detail=error_message)
    
    try:
        # Parse JSON payload
        cart_data = json.loads(payload.decode('utf-8'))
        
        # Process cart creation
        result = await process_cart_creation(cart_data, x_shopify_shop_domain)
        
        # Log successful processing
        logger.info("Cart creation processed", {
            "shop_domain": x_shopify_shop_domain,
            "cart_id": cart_data.get('id'),
            "customer_id": cart_data.get('customer', {}).get('id'),
            "total_price": cart_data.get('total_price'),
            "item_count": cart_data.get('item_count')
        })
        
        return JSONResponse(content={"status": "success", "event_id": result["event_id"]})
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"Error processing cart creation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def process_cart_creation(cart_data: dict, shop_domain: str):
    """Process cart creation webhook data"""
    
    # Create standardized event
    event_data = {
        "event_id": str(uuid4()),
        "event_type": "cart_create",
        "timestamp": datetime.utcnow().isoformat(),
        "shop_domain": shop_domain,
        "customer_id": extract_customer_id(cart_data),
        "source": "shopify_webhook",
        "data": {
            "cart_id": cart_data.get('id'),
            "cart_token": cart_data.get('token'),
            "total_price": cart_data.get('total_price'),
            "currency": cart_data.get('currency'),
            "item_count": cart_data.get('item_count'),
            "line_items": [
                {
                    "product_id": item.get('product_id'),
                    "variant_id": item.get('variant_id'),
                    "title": item.get('title'),
                    "quantity": item.get('quantity'),
                    "price": item.get('price'),
                    "sku": item.get('sku')
                }
                for item in cart_data.get('line_items', [])
            ]
        }
    }
    
    # Publish to Redis
    redis_client = await get_redis_client()
    await redis_client.publish_event("cart_events", event_data)
    
    return {"event_id": event_data["event_id"]}

def extract_customer_id(webhook_data: dict) -> Optional[str]:
    """Extract customer ID from webhook data"""
    customer = webhook_data.get('customer')
    if customer:
        if isinstance(customer, dict):
            return str(customer.get('id'))
        return str(customer)
    return None
```

## 🔄 Event Processing Examples

### Cart Abandonment Detection

```python
# cart_abandonment_processor.py
from datetime import datetime, timedelta
import asyncio

class CartAbandonmentProcessor:
    def __init__(self):
        self.cart_sessions = {}
        self.abandonment_threshold = 30 * 60  # 30 minutes
    
    async def process_cart_event(self, event_data: dict):
        """Process cart-related events and detect abandonment"""
        
        event_type = event_data.get('event_type')
        cart_id = event_data.get('data', {}).get('cart_id')
        customer_id = event_data.get('customer_id')
        shop_domain = event_data.get('shop_domain')
        
        if not cart_id:
            return
        
        session_key = f"{shop_domain}:{cart_id}"
        
        if event_type == 'cart_create':
            await self.handle_cart_creation(session_key, event_data)
        elif event_type == 'cart_update':
            await self.handle_cart_update(session_key, event_data)
        elif event_type == 'checkout_create':
            await self.handle_checkout_started(session_key, event_data)
        elif event_type == 'order_create':
            await self.handle_order_completed(session_key, event_data)
    
    async def handle_cart_creation(self, session_key: str, event_data: dict):
        """Handle new cart creation"""
        
        cart_session = {
            'cart_id': event_data.get('data', {}).get('cart_id'),
            'customer_id': event_data.get('customer_id'),
            'shop_domain': event_data.get('shop_domain'),
            'created_at': datetime.utcnow(),
            'last_activity': datetime.utcnow(),
            'total_price': event_data.get('data', {}).get('total_price', '0'),
            'item_count': event_data.get('data', {}).get('item_count', 0),
            'line_items': event_data.get('data', {}).get('line_items', []),
            'status': 'active',
            'checkout_started': False,
            'order_completed': False,
            'abandonment_emails_sent': 0
        }
        
        self.cart_sessions[session_key] = cart_session
        
        # Schedule abandonment check
        asyncio.create_task(
            self.schedule_abandonment_check(session_key, delay=self.abandonment_threshold)
        )
        
        logger.info("Cart session created", {
            "cart_id": cart_session['cart_id'],
            "customer_id": cart_session['customer_id'],
            "total_price": cart_session['total_price'],
            "item_count": cart_session['item_count']
        })
    
    async def handle_cart_update(self, session_key: str, event_data: dict):
        """Handle cart updates"""
        
        if session_key in self.cart_sessions:
            session = self.cart_sessions[session_key]
            session['last_activity'] = datetime.utcnow()
            session['total_price'] = event_data.get('data', {}).get('total_price', session['total_price'])
            session['item_count'] = event_data.get('data', {}).get('item_count', session['item_count'])
            session['line_items'] = event_data.get('data', {}).get('line_items', session['line_items'])
            
            logger.info("Cart session updated", {
                "cart_id": session['cart_id'],
                "new_total": session['total_price'],
                "new_item_count": session['item_count']
            })
    
    async def handle_checkout_started(self, session_key: str, event_data: dict):
        """Handle checkout initiation"""
        
        if session_key in self.cart_sessions:
            session = self.cart_sessions[session_key]
            session['checkout_started'] = True
            session['last_activity'] = datetime.utcnow()
            session['status'] = 'checkout_started'
            
            logger.info("Checkout started", {
                "cart_id": session['cart_id'],
                "customer_id": session['customer_id']
            })
    
    async def handle_order_completed(self, session_key: str, event_data: dict):
        """Handle successful order completion"""
        
        if session_key in self.cart_sessions:
            session = self.cart_sessions[session_key]
            session['order_completed'] = True
            session['status'] = 'converted'
            session['order_id'] = event_data.get('data', {}).get('order_id')
            
            logger.info("Order completed - cart converted", {
                "cart_id": session['cart_id'],
                "order_id": session['order_id'],
                "customer_id": session['customer_id'],
                "final_total": session['total_price']
            })
            
            # Clean up session after successful conversion
            del self.cart_sessions[session_key]
    
    async def schedule_abandonment_check(self, session_key: str, delay: int):
        """Schedule abandonment check after delay"""
        
        await asyncio.sleep(delay)
        
        if session_key in self.cart_sessions:
            session = self.cart_sessions[session_key]
            
            # Check if cart is still abandoned
            time_since_activity = (datetime.utcnow() - session['last_activity']).total_seconds()
            
            if (time_since_activity >= self.abandonment_threshold and 
                not session['order_completed'] and 
                session['abandonment_emails_sent'] < 3):
                
                await self.trigger_abandonment_recovery(session)
    
    async def trigger_abandonment_recovery(self, session: dict):
        """Trigger cart abandonment recovery actions"""
        
        abandonment_data = {
            'cart_id': session['cart_id'],
            'customer_id': session['customer_id'],
            'shop_domain': session['shop_domain'],
            'total_price': session['total_price'],
            'item_count': session['item_count'],
            'line_items': session['line_items'],
            'time_since_creation': (datetime.utcnow() - session['created_at']).total_seconds(),
            'checkout_started': session['checkout_started'],
            'abandonment_sequence': session['abandonment_emails_sent'] + 1
        }
        
        # Publish abandonment event
        redis_client = await get_redis_client()
        await redis_client.publish_event("cart_abandonment", abandonment_data)
        
        # Update session
        session['abandonment_emails_sent'] += 1
        session['status'] = 'abandoned'
        
        logger.warning("Cart abandonment detected", abandonment_data)
        
        # Schedule next check if under limit
        if session['abandonment_emails_sent'] < 3:
            asyncio.create_task(
                self.schedule_abandonment_check(
                    f"{session['shop_domain']}:{session['cart_id']}", 
                    delay=24 * 60 * 60  # 24 hours later
                )
            )
    
    async def cleanup_expired_sessions(self):
        """Clean up old cart sessions"""
        
        cutoff_time = datetime.utcnow() - timedelta(days=7)
        expired_keys = []
        
        for session_key, session in self.cart_sessions.items():
            if session['created_at'] < cutoff_time:
                expired_keys.append(session_key)
        
        for key in expired_keys:
            del self.cart_sessions[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cart sessions")

# Usage in event processor
cart_processor = CartAbandonmentProcessor()

async def process_cart_event(channel: str, event_data: dict):
    """Main event processing function"""
    
    event_type = event_data.get('event_type', '')
    
    if event_type in ['cart_create', 'cart_update', 'checkout_create', 'order_create']:
        await cart_processor.process_cart_event(event_data)
    
    # Log all events
    logger.info("Event processed", {
        "channel": channel,
        "event_type": event_type,
        "event_id": event_data.get('event_id'),
        "shop_domain": event_data.get('shop_domain')
    })
```

## 📧 Recovery Email Integration

### Email Template Examples

```python
# email_templates.py
from string import Template
from typing import Dict, Any

class RecoveryEmailTemplates:
    
    @staticmethod
    def get_first_abandonment_template() -> Dict[str, str]:
        """First abandonment email - sent 30 minutes after abandonment"""
        return {
            "subject": "You left something in your cart at $shop_name",
            "html_body": Template("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Complete Your Purchase</title>
                <style>
                    .container { max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }
                    .header { background-color: #f8f9fa; padding: 20px; text-align: center; }
                    .content { padding: 30px 20px; }
                    .product-item { border: 1px solid #eee; padding: 15px; margin: 10px 0; }
                    .cta-button { 
                        background-color: #007bff; 
                        color: white; 
                        padding: 12px 30px; 
                        text-decoration: none; 
                        border-radius: 5px; 
                        display: inline-block;
                        margin: 20px 0;
                    }
                    .footer { background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>$shop_name</h1>
                    </div>
                    
                    <div class="content">
                        <h2>Don't forget about your items!</h2>
                        
                        <p>Hi $customer_name,</p>
                        
                        <p>You left some great items in your shopping cart. We wanted to remind you before they're gone!</p>
                        
                        <div class="cart-items">
                            $line_items_html
                        </div>
                        
                        <p><strong>Cart Total: $total_price</strong></p>
                        
                        <a href="$checkout_url" class="cta-button">Complete Your Purchase</a>
                        
                        <p>This cart will be saved for 7 days. After that, we can't guarantee these items will still be available.</p>
                        
                        <p>If you have any questions, feel free to reply to this email or contact our support team.</p>
                        
                        <p>Happy shopping!<br>The $shop_name Team</p>
                    </div>
                    
                    <div class="footer">
                        <p>&copy; 2023 $shop_name. All rights reserved.</p>
                        <p><a href="$unsubscribe_url">Unsubscribe</a> | <a href="$shop_url">Visit Store</a></p>
                    </div>
                </div>
            </body>
            </html>
            """),
            
            "text_body": Template("""
            Don't forget about your items!
            
            Hi $customer_name,
            
            You left some great items in your shopping cart at $shop_name:
            
            $line_items_text
            
            Cart Total: $total_price
            
            Complete your purchase: $checkout_url
            
            This cart will be saved for 7 days. After that, we can't guarantee these items will still be available.
            
            If you have any questions, feel free to reply to this email.
            
            Happy shopping!
            The $shop_name Team
            
            Unsubscribe: $unsubscribe_url
            """)
        }
    
    @staticmethod
    def get_discount_abandonment_template() -> Dict[str, str]:
        """Second abandonment email with discount - sent 24 hours later"""
        return {
            "subject": "Still thinking it over? Here's 10% off your cart",
            "html_body": Template("""
            <!DOCTYPE html>
            <html>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>$shop_name</h1>
                    </div>
                    
                    <div class="content">
                        <h2>We miss you! Here's 10% off</h2>
                        
                        <p>Hi $customer_name,</p>
                        
                        <p>We noticed you were interested in these items. To help you complete your purchase, we're offering you <strong>10% off your entire cart!</strong></p>
                        
                        <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; text-align: center; margin: 20px 0;">
                            <h3>Use code: <span style="font-size: 24px; color: #e17055;">SAVE10</span></h3>
                            <p>Valid for the next 48 hours</p>
                        </div>
                        
                        <div class="cart-items">
                            $line_items_html
                        </div>
                        
                        <p>
                            <s>Original Total: $total_price</s><br>
                            <strong>With Discount: $discounted_price</strong>
                        </p>
                        
                        <a href="$checkout_url?discount=SAVE10" class="cta-button">Get My 10% Discount</a>
                        
                        <p><small>*Discount valid for 48 hours. Cannot be combined with other offers.</small></p>
                    </div>
                    
                    <div class="footer">
                        <p>&copy; 2023 $shop_name. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """)
        }
    
    @staticmethod
    def get_final_abandonment_template() -> Dict[str, str]:
        """Final abandonment email - sent 3 days later"""
        return {
            "subject": "Last chance - your cart expires soon",
            "html_body": Template("""
            <!DOCTYPE html>
            <html>
            <body>
                <div class="container">
                    <div class="content">
                        <h2>⏰ Your cart expires in 24 hours</h2>
                        
                        <p>Hi $customer_name,</p>
                        
                        <p>This is your final reminder that these items are waiting for you:</p>
                        
                        <div class="cart-items">
                            $line_items_html
                        </div>
                        
                        <div style="background-color: #ffe6e6; border: 1px solid #ffb3b3; padding: 15px; margin: 20px 0;">
                            <h3>⚠️ Cart expires in 24 hours</h3>
                            <p>After that, we can't guarantee these items will still be available at this price.</p>
                        </div>
                        
                        <a href="$checkout_url" class="cta-button">Complete Purchase Now</a>
                        
                        <p>If you're not ready to purchase, we understand. You can always browse our latest collection at <a href="$shop_url">$shop_name</a>.</p>
                        
                        <p>Thanks for considering us!</p>
                    </div>
                </div>
            </body>
            </html>
            """)
        }
    
    @staticmethod
    def format_line_items_html(line_items: list) -> str:
        """Format line items for HTML email"""
        html_items = []
        
        for item in line_items:
            html_items.append(f"""
            <div class="product-item">
                <h4>{item.get('title', 'Product')}</h4>
                <p>Quantity: {item.get('quantity', 1)} × ${item.get('price', '0.00')}</p>
                {f"<p>SKU: {item.get('sku')}</p>" if item.get('sku') else ""}
            </div>
            """)
        
        return "".join(html_items)
    
    @staticmethod
    def format_line_items_text(line_items: list) -> str:
        """Format line items for plain text email"""
        text_items = []
        
        for item in line_items:
            text_items.append(
                f"- {item.get('title', 'Product')} "
                f"(Qty: {item.get('quantity', 1)}) - ${item.get('price', '0.00')}"
            )
        
        return "\n".join(text_items)

# Email sending integration
async def send_abandonment_email(cart_data: dict, template_type: str = "first"):
    """Send cart abandonment recovery email"""
    
    templates = RecoveryEmailTemplates()
    
    if template_type == "first":
        template = templates.get_first_abandonment_template()
    elif template_type == "discount":
        template = templates.get_discount_abandonment_template()
    elif template_type == "final":
        template = templates.get_final_abandonment_template()
    else:
        raise ValueError(f"Unknown template type: {template_type}")
    
    # Prepare template variables
    customer_name = "there"  # Default fallback
    if cart_data.get('customer_id'):
        # Fetch customer name from Shopify API
        customer_name = await get_customer_name(cart_data['customer_id'])
    
    total_price = float(cart_data.get('total_price', '0'))
    discounted_price = total_price * 0.9  # 10% discount
    
    template_vars = {
        'shop_name': 'Your Store Name',
        'customer_name': customer_name,
        'total_price': f"${total_price:.2f}",
        'discounted_price': f"${discounted_price:.2f}",
        'line_items_html': templates.format_line_items_html(cart_data.get('line_items', [])),
        'line_items_text': templates.format_line_items_text(cart_data.get('line_items', [])),
        'checkout_url': f"https://your-store.myshopify.com/cart/{cart_data.get('cart_token')}",
        'shop_url': 'https://your-store.myshopify.com',
        'unsubscribe_url': 'https://your-store.myshopify.com/unsubscribe'
    }
    
    # Format email content
    subject = Template(template['subject']).safe_substitute(template_vars)
    html_body = template['html_body'].safe_substitute(template_vars)
    text_body = template.get('text_body', Template("")).safe_substitute(template_vars)
    
    # Send email (integrate with your email provider)
    await send_email(
        to=cart_data.get('customer_email'),
        subject=subject,
        html_body=html_body,
        text_body=text_body
    )
    
    logger.info("Abandonment email sent", {
        "cart_id": cart_data.get('cart_id'),
        "customer_id": cart_data.get('customer_id'),
        "template_type": template_type,
        "email": cart_data.get('customer_email')
    })
```

These webhook examples provide comprehensive coverage for integrating with Shopify's webhook system, including proper validation, event processing, cart abandonment detection, and recovery email templates.