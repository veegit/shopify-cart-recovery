from datetime import datetime
from typing import Optional, Dict, Any
from uuid import uuid4
from pydantic import BaseModel, Field, validator


class BaseWebPixelEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None
    customer_id: Optional[str] = None
    shop_domain: Optional[str] = None
    url: str
    user_agent: Optional[str] = None
    sequence_number: Optional[int] = None
    
    def to_redis_event(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.__class__.__name__.replace("Model", "").lower(),
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "customer_id": self.customer_id,
            "shop_domain": self.shop_domain,
            "url": self.url,
            "user_agent": self.user_agent,
            "sequence_number": self.sequence_number,
            "source": "web_pixels",
            "data": self.dict(exclude={
                "event_id", "timestamp", "session_id", "customer_id", 
                "shop_domain", "user_agent", "sequence_number"
            })
        }


class ClickedEventModel(BaseWebPixelEvent):
    clientX: int = Field(..., ge=0, description="Mouse X coordinate")
    clientY: int = Field(..., ge=0, description="Mouse Y coordinate")
    element_id: Optional[str] = None
    element_class: Optional[str] = None
    element_tag: str = Field(..., min_length=1)
    element_href: Optional[str] = None
    element_text: Optional[str] = None
    element_value: Optional[str] = None
    target_selector: Optional[str] = None
    page_x: Optional[int] = None
    page_y: Optional[int] = None
    
    @validator('clientX', 'clientY')
    def validate_coordinates(cls, v):
        if v < 0 or v > 10000:
            raise ValueError('Invalid coordinate value')
        return v
    
    @validator('element_tag')
    def validate_tag(cls, v):
        valid_tags = ['a', 'button', 'input', 'div', 'span', 'img', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td', 'th']
        if v.lower() not in valid_tags:
            return v
        return v.lower()


class InputChangedEventModel(BaseWebPixelEvent):
    element_id: Optional[str] = None
    element_name: Optional[str] = None
    element_type: str = Field(..., min_length=1)
    element_value: str
    previous_value: Optional[str] = None
    element_selector: Optional[str] = None
    form_id: Optional[str] = None
    
    @validator('element_type')
    def validate_input_type(cls, v):
        valid_types = ['text', 'email', 'password', 'number', 'tel', 'url', 'search', 'textarea', 'select']
        if v.lower() not in valid_types:
            return v
        return v.lower()


class InputFocusedEventModel(BaseWebPixelEvent):
    element_id: Optional[str] = None
    element_name: Optional[str] = None
    element_type: str = Field(..., min_length=1)
    element_selector: Optional[str] = None
    form_id: Optional[str] = None
    focus_timestamp: datetime = Field(default_factory=datetime.utcnow)


class InputBlurredEventModel(BaseWebPixelEvent):
    element_id: Optional[str] = None
    element_name: Optional[str] = None
    element_type: str = Field(..., min_length=1)
    element_selector: Optional[str] = None
    form_id: Optional[str] = None
    blur_timestamp: datetime = Field(default_factory=datetime.utcnow)
    focus_duration: Optional[int] = Field(None, ge=0, description="Duration in milliseconds")


class FormSubmittedEventModel(BaseWebPixelEvent):
    form_id: Optional[str] = None
    form_name: Optional[str] = None
    form_action: Optional[str] = None
    form_method: str = Field(default="POST")
    field_count: int = Field(..., ge=0)
    filled_fields: int = Field(..., ge=0)
    form_selector: Optional[str] = None
    submission_method: str = Field(default="click")
    
    @validator('form_method')
    def validate_method(cls, v):
        return v.upper() if v else "POST"
    
    @validator('filled_fields', 'field_count')
    def validate_field_counts(cls, v, values):
        if 'field_count' in values and v > values['field_count']:
            raise ValueError('Filled fields cannot exceed total field count')
        return v


class PageViewedEventModel(BaseWebPixelEvent):
    page_title: Optional[str] = None
    referrer: Optional[str] = None
    page_type: Optional[str] = None
    viewport_width: Optional[int] = Field(None, ge=0)
    viewport_height: Optional[int] = Field(None, ge=0)
    screen_width: Optional[int] = Field(None, ge=0)
    screen_height: Optional[int] = Field(None, ge=0)
    scroll_depth: Optional[float] = Field(None, ge=0.0, le=1.0)
    time_on_page: Optional[int] = Field(None, ge=0, description="Time in milliseconds")


class WebPixelEventProcessor:
    def __init__(self):
        self.session_cache = {}
    
    def validate_payload(self, event_type: str, payload: Dict[str, Any]) -> BaseWebPixelEvent:
        model_map = {
            "clicked": ClickedEventModel,
            "input_changed": InputChangedEventModel,
            "input_focused": InputFocusedEventModel,
            "input_blurred": InputBlurredEventModel,
            "form_submitted": FormSubmittedEventModel,
            "page_viewed": PageViewedEventModel
        }
        
        model_class = model_map.get(event_type)
        if not model_class:
            raise ValueError(f"Unknown event type: {event_type}")
        
        return model_class(**payload)
    
    def enrich_event(self, event: BaseWebPixelEvent, session_context: Optional[Dict[str, Any]] = None) -> BaseWebPixelEvent:
        if session_context:
            if not event.session_id and session_context.get("session_id"):
                event.session_id = session_context["session_id"]
            if not event.customer_id and session_context.get("customer_id"):
                event.customer_id = session_context["customer_id"]
            if not event.shop_domain and session_context.get("shop_domain"):
                event.shop_domain = session_context["shop_domain"]
        
        if event.session_id and event.session_id not in self.session_cache:
            self.session_cache[event.session_id] = {
                "first_seen": event.timestamp,
                "last_seen": event.timestamp,
                "event_count": 0
            }
        
        if event.session_id:
            session_data = self.session_cache[event.session_id]
            session_data["last_seen"] = event.timestamp
            session_data["event_count"] += 1
            event.sequence_number = session_data["event_count"]
        
        return event
    
    def deduplicate_event(self, event: BaseWebPixelEvent) -> bool:
        if not event.session_id:
            return True
        
        cache_key = f"{event.session_id}:{event.event_id}"
        if cache_key in self.session_cache:
            return False
        
        self.session_cache[cache_key] = True
        return True
    
    def process_event(self, event_type: str, payload: Dict[str, Any], session_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        event = self.validate_payload(event_type, payload)
        event = self.enrich_event(event, session_context)
        
        if not self.deduplicate_event(event):
            raise ValueError("Duplicate event detected")
        
        return event.to_redis_event()