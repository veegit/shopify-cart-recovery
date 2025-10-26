import asyncio
import signal
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.redis_client import get_redis_client
from shared.logging_config import get_logger
from shared.config import get_settings

logger = get_logger("event_processor")
settings = get_settings()


@dataclass
class SessionJourney:
    session_id: str
    customer_id: Optional[str] = None
    shop_domain: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    dom_events: List[Dict[str, Any]] = field(default_factory=list)
    webhook_events: List[Dict[str, Any]] = field(default_factory=list)
    page_views: List[Dict[str, Any]] = field(default_factory=list)
    click_pattern: List[Dict[str, Any]] = field(default_factory=list)
    form_interactions: List[Dict[str, Any]] = field(default_factory=list)
    conversion_events: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_event(self, event: Dict[str, Any]):
        self.last_activity = datetime.utcnow()
        event_type = event.get("event_type", "")
        
        if event.get("source") == "web_pixels":
            self.dom_events.append(event)
            
            if event_type == "clicked":
                self.click_pattern.append(event)
            elif event_type in ["input_changed", "input_focused", "input_blurred", "form_submitted"]:
                self.form_interactions.append(event)
            elif event_type == "page_viewed":
                self.page_views.append(event)
        
        elif event.get("source") == "shopify_webhook":
            self.webhook_events.append(event)
            
            if event_type in ["order_create", "order_paid"]:
                self.conversion_events.append(event)
    
    def get_session_duration(self) -> float:
        return (self.last_activity - self.start_time).total_seconds()
    
    def get_engagement_score(self) -> float:
        duration_minutes = self.get_session_duration() / 60
        click_density = len(self.click_pattern) / max(duration_minutes, 1)
        form_engagement = len(self.form_interactions) / max(len(self.page_views), 1)
        
        base_score = min(duration_minutes * 0.1, 1.0)
        interaction_bonus = min(click_density * 0.1, 0.5)
        form_bonus = min(form_engagement * 0.3, 0.3)
        
        return min(base_score + interaction_bonus + form_bonus, 1.0)
    
    def detect_abandonment_signals(self) -> Dict[str, Any]:
        signals = {
            "rapid_clicks": False,
            "form_abandonment": False,
            "cart_without_checkout": False,
            "hesitation_pattern": False,
            "exit_intent": False
        }

        if len(self.click_pattern) > 10:
            try:
                click_times = []
                for c in self.click_pattern[-10:]:
                    if "timestamp" in c:
                        try:
                            click_times.append(datetime.fromisoformat(c["timestamp"]))
                        except (ValueError, TypeError):
                            # Skip malformed timestamps
                            continue

                if len(click_times) > 1:
                    time_diffs = [(click_times[i] - click_times[i-1]).total_seconds() for i in range(1, len(click_times))]
                    avg_time_between_clicks = sum(time_diffs) / len(time_diffs)
                    signals["rapid_clicks"] = avg_time_between_clicks < 2.0
            except Exception:
                # Silently skip if timestamp parsing fails
                pass
        
        form_events = [e for e in self.form_interactions if e["event_type"] in ["input_focused", "input_changed"]]
        form_submissions = [e for e in self.form_interactions if e["event_type"] == "form_submitted"]
        signals["form_abandonment"] = len(form_events) > 3 and len(form_submissions) == 0
        
        cart_events = [e for e in self.webhook_events if "cart" in e["event_type"]]
        checkout_events = [e for e in self.webhook_events if "checkout" in e["event_type"]]
        signals["cart_without_checkout"] = len(cart_events) > 0 and len(checkout_events) == 0
        
        return signals


class BehaviorAnalyzer:
    def __init__(self):
        self.click_patterns = defaultdict(list)
        self.session_metrics = {}
    
    def analyze_click_pattern(self, session_id: str, click_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        if len(click_events) < 2:
            return {"pattern_type": "insufficient_data"}

        coordinates = []
        for e in click_events:
            if "data" in e and isinstance(e["data"], dict):
                data = e["data"]
                if "clientX" in data and "clientY" in data:
                    try:
                        coordinates.append((int(data["clientX"]), int(data["clientY"])))
                    except (ValueError, TypeError):
                        # Skip invalid coordinates
                        continue

        if len(coordinates) < 2:
            return {"pattern_type": "no_coordinates"}
        
        movements = []
        for i in range(1, len(coordinates)):
            x_diff = coordinates[i][0] - coordinates[i-1][0]
            y_diff = coordinates[i][1] - coordinates[i-1][1]
            distance = (x_diff**2 + y_diff**2)**0.5
            movements.append(distance)
        
        avg_movement = sum(movements) / len(movements)
        large_movements = sum(1 for m in movements if m > 200)
        
        pattern_analysis = {
            "avg_movement_distance": round(avg_movement, 2),
            "large_movements": large_movements,
            "click_frequency": len(click_events),
            "pattern_type": "normal"
        }
        
        if avg_movement < 50 and large_movements == 0:
            pattern_analysis["pattern_type"] = "focused"
        elif large_movements > len(movements) * 0.6:
            pattern_analysis["pattern_type"] = "scattered"
        elif avg_movement > 300:
            pattern_analysis["pattern_type"] = "erratic"
        
        return pattern_analysis
    
    def analyze_form_behavior(self, form_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        focus_events = [e for e in form_events if e["event_type"] == "input_focused"]
        blur_events = [e for e in form_events if e["event_type"] == "input_blurred"]
        change_events = [e for e in form_events if e["event_type"] == "input_changed"]
        submit_events = [e for e in form_events if e["event_type"] == "form_submitted"]
        
        total_focus_time = 0
        for blur_event in blur_events:
            if "focus_duration" in blur_event.get("data", {}):
                total_focus_time += blur_event["data"]["focus_duration"]
        
        return {
            "total_fields_interacted": len(set(e.get("data", {}).get("element_id") for e in focus_events)),
            "total_focus_time_ms": total_focus_time,
            "form_changes": len(change_events),
            "form_submissions": len(submit_events),
            "abandonment_rate": 1 - (len(submit_events) / max(len(focus_events), 1)),
            "avg_field_focus_time": total_focus_time / max(len(blur_events), 1)
        }


class EventProcessor:
    def __init__(self):
        self.sessions = {}
        self.behavior_analyzer = BehaviorAnalyzer()
        self.processing_stats = {
            "total_events": 0,
            "dom_events": 0,
            "webhook_events": 0,
            "session_correlations": 0,
            "insights_generated": 0
        }
        self.running = False
    
    async def process_event(self, channel: str, event_data: Dict[str, Any]):
        try:
            self.processing_stats["total_events"] += 1
            
            event_source = event_data.get("source", "unknown")
            session_id = event_data.get("session_id")
            customer_id = event_data.get("customer_id")
            
            if session_id:
                if session_id not in self.sessions:
                    self.sessions[session_id] = SessionJourney(
                        session_id=session_id,
                        customer_id=customer_id,
                        shop_domain=event_data.get("shop_domain")
                    )
                
                journey = self.sessions[session_id]
                journey.add_event(event_data)
                
                if customer_id and not journey.customer_id:
                    journey.customer_id = customer_id
                
                await self.analyze_session_patterns(journey, event_data)
            
            if event_source == "web_pixels":
                await self.process_dom_event(event_data)
                self.processing_stats["dom_events"] += 1
            elif event_source == "shopify_webhook":
                await self.process_webhook_event(event_data)
                self.processing_stats["webhook_events"] += 1
            
        except Exception as e:
            logger.error(f"Error processing event from {channel}: {e}", {
                "channel": channel,
                "event_data": event_data,
                "error": str(e)
            })
    
    async def process_dom_event(self, event: Dict[str, Any]):
        event_type = event.get("event_type", "")
        data = event.get("data", {})
        
        if event_type == "clicked":
            await self.analyze_click_event(event)
        elif event_type in ["input_focused", "input_changed", "input_blurred"]:
            await self.analyze_input_event(event)
        elif event_type == "form_submitted":
            await self.analyze_form_submission(event)
        elif event_type == "page_viewed":
            await self.analyze_page_view(event)
        
        logger.info(f"Processed DOM event: {event_type}", {
            "event_type": event_type,
            "session_id": event.get("session_id"),
            "customer_id": event.get("customer_id"),
            "element_details": data.get("element_tag") or data.get("element_type"),
            "coordinates": f"({data.get('clientX')}, {data.get('clientY')})" if data.get('clientX') else None
        })
    
    async def process_webhook_event(self, event: Dict[str, Any]):
        event_type = event.get("event_type", "")
        data = event.get("data", {})
        
        logger.info(f"Processed webhook event: {event_type}", {
            "event_type": event_type,
            "customer_id": event.get("customer_id"),
            "shop_domain": event.get("shop_domain"),
            "cart_id": data.get("cart_id"),
            "checkout_id": data.get("checkout_id"),
            "order_id": data.get("order_id"),
            "total_price": data.get("total_price")
        })
        
        if event_type in ["order_create", "order_paid"]:
            await self.log_conversion_event(event)
    
    async def analyze_click_event(self, event: Dict[str, Any]):
        data = event.get("data", {})
        session_id = event.get("session_id")
        
        if session_id and session_id in self.sessions:
            journey = self.sessions[session_id]
            click_analysis = self.behavior_analyzer.analyze_click_pattern(
                session_id, journey.click_pattern
            )
            
            logger.info("Click pattern analysis", {
                "session_id": session_id,
                "click_analysis": click_analysis,
                "element_clicked": data.get("element_tag"),
                "coordinates": f"({data.get('clientX')}, {data.get('clientY')})"
            })
    
    async def analyze_input_event(self, event: Dict[str, Any]):
        data = event.get("data", {})
        
        logger.info("Form interaction detected", {
            "event_type": event.get("event_type"),
            "session_id": event.get("session_id"),
            "element_type": data.get("element_type"),
            "form_id": data.get("form_id"),
            "focus_duration": data.get("focus_duration")
        })
    
    async def analyze_form_submission(self, event: Dict[str, Any]):
        data = event.get("data", {})
        session_id = event.get("session_id")
        
        if session_id and session_id in self.sessions:
            journey = self.sessions[session_id]
            form_analysis = self.behavior_analyzer.analyze_form_behavior(journey.form_interactions)
            
            logger.info("Form submission analysis", {
                "session_id": session_id,
                "form_analysis": form_analysis,
                "form_id": data.get("form_id"),
                "field_count": data.get("field_count"),
                "filled_fields": data.get("filled_fields")
            })
    
    async def analyze_page_view(self, event: Dict[str, Any]):
        data = event.get("data", {})
        
        logger.info("Page engagement tracked", {
            "session_id": event.get("session_id"),
            "url": event.get("url"),
            "time_on_page": data.get("time_on_page"),
            "scroll_depth": data.get("scroll_depth"),
            "viewport_size": f"{data.get('viewport_width')}x{data.get('viewport_height')}"
        })
    
    async def analyze_session_patterns(self, journey: SessionJourney, latest_event: Dict[str, Any]):
        session_duration = journey.get_session_duration()
        engagement_score = journey.get_engagement_score()
        abandonment_signals = journey.detect_abandonment_signals()
        
        has_cart_activity = any("cart" in e["event_type"] for e in journey.webhook_events)
        has_checkout_activity = any("checkout" in e["event_type"] for e in journey.webhook_events)
        has_conversion = any("order" in e["event_type"] for e in journey.conversion_events)
        
        intent_level = "low"
        if engagement_score > 0.7 or has_checkout_activity:
            intent_level = "high"
        elif engagement_score > 0.4 or has_cart_activity:
            intent_level = "medium"
        
        insights = {
            "session_id": journey.session_id,
            "customer_id": journey.customer_id,
            "session_duration_minutes": round(session_duration / 60, 2),
            "engagement_score": round(engagement_score, 3),
            "intent_level": intent_level,
            "total_events": len(journey.dom_events) + len(journey.webhook_events),
            "dom_event_count": len(journey.dom_events),
            "webhook_event_count": len(journey.webhook_events),
            "page_views": len(journey.page_views),
            "clicks": len(journey.click_pattern),
            "form_interactions": len(journey.form_interactions),
            "has_cart_activity": has_cart_activity,
            "has_checkout_activity": has_checkout_activity,
            "converted": has_conversion,
            "abandonment_signals": abandonment_signals
        }
        
        if any(abandonment_signals.values()) and not has_conversion:
            logger.warning("Cart abandonment signals detected", {
                "insights": insights,
                "abandonment_signals": abandonment_signals
            })
            self.processing_stats["insights_generated"] += 1
        
        if latest_event.get("source") == "shopify_webhook" and latest_event.get("event_type") in ["order_create", "order_paid"]:
            await self.log_conversion_correlation(journey, insights)
    
    async def log_conversion_event(self, event: Dict[str, Any]):
        session_id = event.get("session_id")
        customer_id = event.get("customer_id")
        
        if session_id and session_id in self.sessions:
            journey = self.sessions[session_id]
            
            logger.info("Conversion event with behavioral correlation", {
                "event_type": event.get("event_type"),
                "customer_id": customer_id,
                "session_id": session_id,
                "session_duration_minutes": round(journey.get_session_duration() / 60, 2),
                "engagement_score": round(journey.get_engagement_score(), 3),
                "total_clicks": len(journey.click_pattern),
                "form_interactions": len(journey.form_interactions),
                "page_views": len(journey.page_views),
                "order_value": event.get("data", {}).get("total_price")
            })
            
            self.processing_stats["session_correlations"] += 1
    
    async def log_conversion_correlation(self, journey: SessionJourney, insights: Dict[str, Any]):
        click_analysis = self.behavior_analyzer.analyze_click_pattern(
            journey.session_id, journey.click_pattern
        )
        form_analysis = self.behavior_analyzer.analyze_form_behavior(journey.form_interactions)
        
        logger.info("Conversion with full behavioral analysis", {
            "session_insights": insights,
            "click_behavior": click_analysis,
            "form_behavior": form_analysis,
            "journey_summary": {
                "pages_visited": len(journey.page_views),
                "total_dom_events": len(journey.dom_events),
                "business_events": len(journey.webhook_events),
                "conversion_path": [e["event_type"] for e in journey.webhook_events]
            }
        })
    
    def cleanup_expired_sessions(self):
        cutoff_time = datetime.utcnow() - timedelta(hours=4)
        expired_sessions = [
            sid for sid, journey in self.sessions.items()
            if journey.last_activity < cutoff_time
        ]
        
        for sid in expired_sessions:
            journey = self.sessions[sid]
            
            if not journey.conversion_events and journey.webhook_events:
                logger.info("Session expired without conversion", {
                    "session_id": sid,
                    "customer_id": journey.customer_id,
                    "duration_minutes": round(journey.get_session_duration() / 60, 2),
                    "engagement_score": round(journey.get_engagement_score(), 3),
                    "abandonment_signals": journey.detect_abandonment_signals(),
                    "final_events": [e["event_type"] for e in journey.webhook_events[-3:]]
                })
            
            del self.sessions[sid]
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    async def start_processing(self):
        self.running = True
        redis_client = await get_redis_client()
        
        channels = [
            "cart_events", "checkout_events", "order_events", "customer_events",
            "dom_events", "click_events", "form_events"
        ]
        
        logger.info("Starting event processor", {"channels": channels})
        
        async def cleanup_task():
            while self.running:
                await asyncio.sleep(300)  # 5 minutes
                self.cleanup_expired_sessions()
        
        cleanup_coroutine = asyncio.create_task(cleanup_task())
        
        try:
            await redis_client.subscribe_to_events(channels, self.process_event)
        except Exception as e:
            logger.error(f"Event processing stopped: {e}")
        finally:
            cleanup_coroutine.cancel()
    
    def stop_processing(self):
        self.running = False
        logger.info("Event processor stopped", {"final_stats": self.processing_stats})


event_processor = EventProcessor()


def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}, shutting down gracefully")
    event_processor.stop_processing()


async def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Enhanced Event Processor starting")
    
    try:
        await event_processor.start_processing()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Event processor crashed: {e}")
    finally:
        event_processor.stop_processing()
        from shared.redis_client import close_redis_client
        await close_redis_client()


if __name__ == "__main__":
    asyncio.run(main())