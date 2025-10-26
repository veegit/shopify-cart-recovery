from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator


class EventType(str, Enum):
    CART_CREATE = "cart_create"
    CART_UPDATE = "cart_update"
    CHECKOUT_CREATE = "checkout_create"
    CHECKOUT_UPDATE = "checkout_update"
    CUSTOMER_CREATE = "customer_create"
    CUSTOMER_UPDATE = "customer_update"
    ORDER_CREATE = "order_create"
    ORDER_PAID = "order_paid"
    ORDER_FULFILLED = "order_fulfilled"


class BaseEventModel(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    shop_domain: str = Field(..., min_length=1)
    customer_id: Optional[str] = None
    session_id: Optional[str] = None
    
    def to_redis_event(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "shop_domain": self.shop_domain,
            "customer_id": self.customer_id,
            "session_id": self.session_id,
            "source": "shopify_webhook",
            "data": self.dict(exclude={
                "event_id", "event_type", "timestamp", "shop_domain", 
                "customer_id", "session_id"
            })
        }


class LineItem(BaseModel):
    id: int
    product_id: int
    variant_id: int
    title: str
    quantity: int
    price: str
    sku: Optional[str] = None
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        try:
            return str(Decimal(v))
        except (ValueError, InvalidOperation, TypeError):
            raise ValueError('Invalid price format')


class CartEventModel(BaseEventModel):
    cart_id: str = Field(..., min_length=1)
    cart_token: str = Field(..., min_length=1)
    line_items: List[LineItem] = Field(default_factory=list)
    total_price: str = Field(..., min_length=1)
    total_weight: Optional[int] = None
    item_count: int = Field(..., ge=0)
    currency: str = Field(..., min_length=3, max_length=3)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v):
        return v.upper()

    @field_validator('total_price')
    @classmethod
    def validate_total_price(cls, v):
        try:
            return str(Decimal(v))
        except (ValueError, InvalidOperation, TypeError):
            raise ValueError('Invalid total price format')


class CheckoutEventModel(BaseEventModel):
    checkout_id: str = Field(..., min_length=1)
    checkout_token: str = Field(..., min_length=1)
    line_items: List[LineItem] = Field(default_factory=list)
    total_price: str = Field(..., min_length=1)
    subtotal_price: str = Field(..., min_length=1)
    total_tax: Optional[str] = None
    currency: str = Field(..., min_length=3, max_length=3)
    email: Optional[str] = None
    phone: Optional[str] = None
    billing_address: Optional[Dict[str, Any]] = None
    shipping_address: Optional[Dict[str, Any]] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v):
        return v.upper()

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v


class CustomerEventModel(BaseEventModel):
    customer_shopify_id: int = Field(..., gt=0)
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    accepts_marketing: bool = False
    orders_count: int = Field(default=0, ge=0)
    total_spent: str = Field(default="0.00")
    tags: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v

    @field_validator('total_spent')
    @classmethod
    def validate_total_spent(cls, v):
        try:
            return str(Decimal(v))
        except (ValueError, InvalidOperation, TypeError):
            raise ValueError('Invalid total spent format')


class OrderEventModel(BaseEventModel):
    order_id: int = Field(..., gt=0)
    order_number: str = Field(..., min_length=1)
    line_items: List[LineItem] = Field(default_factory=list)
    total_price: str = Field(..., min_length=1)
    subtotal_price: str = Field(..., min_length=1)
    total_tax: Optional[str] = None
    currency: str = Field(..., min_length=3, max_length=3)
    financial_status: Optional[str] = None
    fulfillment_status: Optional[str] = None
    email: Optional[str] = None
    billing_address: Optional[Dict[str, Any]] = None
    shipping_address: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v):
        return v.upper()

    @field_validator('total_price', 'subtotal_price')
    @classmethod
    def validate_price_fields(cls, v):
        try:
            return str(Decimal(v))
        except (ValueError, InvalidOperation, TypeError):
            raise ValueError('Invalid price format')

    @field_validator('financial_status')
    @classmethod
    def validate_financial_status(cls, v):
        if v:
            valid_statuses = ['pending', 'authorized', 'partially_paid', 'paid', 'partially_refunded', 'refunded', 'voided']
            if v.lower() not in valid_statuses:
                raise ValueError(f'Invalid financial status: {v}. Must be one of {valid_statuses}')
            return v.lower()
        return v


class EventProcessor:
    def __init__(self):
        self.event_type_map = {
            "carts/create": (CartEventModel, EventType.CART_CREATE),
            "carts/update": (CartEventModel, EventType.CART_UPDATE),
            "checkouts/create": (CheckoutEventModel, EventType.CHECKOUT_CREATE),
            "checkouts/update": (CheckoutEventModel, EventType.CHECKOUT_UPDATE),
            "customers/create": (CustomerEventModel, EventType.CUSTOMER_CREATE),
            "customers/update": (CustomerEventModel, EventType.CUSTOMER_UPDATE),
            "orders/create": (OrderEventModel, EventType.ORDER_CREATE),
            "orders/paid": (OrderEventModel, EventType.ORDER_PAID),
            "orders/fulfilled": (OrderEventModel, EventType.ORDER_FULFILLED),
        }
    
    def process_webhook(self, webhook_topic: str, payload: Dict[str, Any], shop_domain: str) -> Dict[str, Any]:
        if webhook_topic not in self.event_type_map:
            raise ValueError(f"Unsupported webhook topic: {webhook_topic}")
        
        model_class, event_type = self.event_type_map[webhook_topic]
        
        event_data = {
            "event_type": event_type,
            "shop_domain": shop_domain,
            **payload
        }
        
        if "customer" in payload and payload["customer"]:
            customer = payload["customer"]
            if isinstance(customer, dict):
                event_data["customer_id"] = str(customer.get("id"))
            else:
                event_data["customer_id"] = str(customer)
        
        try:
            event = model_class(**event_data)
            redis_event = event.to_redis_event()
            redis_event["processing_timestamp"] = datetime.utcnow().isoformat()
            redis_event["webhook_topic"] = webhook_topic
            
            return redis_event
        
        except Exception as e:
            raise ValueError(f"Failed to process webhook: {e}")
    
    def extract_customer_id(self, payload: Dict[str, Any]) -> Optional[str]:
        if "customer_id" in payload and payload["customer_id"]:
            return str(payload["customer_id"])
        
        if "customer" in payload and payload["customer"]:
            customer = payload["customer"]
            if isinstance(customer, dict):
                return str(customer.get("id"))
            return str(customer)
        
        if "email" in payload and payload["email"]:
            return payload["email"]
        
        return None