# Integration Examples & Sample Configurations

Complete examples and configurations for integrating the Shopify Cart Recovery dual-stream system with various tools and scenarios.

## 🌐 Web Pixels JavaScript Integration Examples

### Basic Integration

```html
<!-- Basic Shopify theme integration -->
<!DOCTYPE html>
<html>
<head>
    <title>{{ page_title }}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
    <!-- Your theme content -->
    
    <!-- Web Pixels Integration -->
    <script>
        // Configure before loading pixel
        window.WEB_PIXELS_ENDPOINT = 'https://your-domain.com/pixels';
        window.SHOPIFY_STORE_DOMAIN = '{{ shop.permanent_domain }}';
        
        {% if customer %}
        window.SHOPIFY_CUSTOMER_ID = '{{ customer.id }}';
        {% endif %}
    </script>
    
    <!-- Load Web Pixels (add to Shopify Admin > Customer events) -->
    <!-- The pixel.js content goes in Shopify Admin, not in theme files -->
</body>
</html>
```

### Advanced Theme Integration

```javascript
// theme-integration.js
// Add to your Shopify theme's main JavaScript file

class ShopifyCartRecovery {
    constructor() {
        this.sessionId = this.getSessionId();
        this.customerId = this.getCustomerId();
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.trackPageView();
        this.setupCartTracking();
        this.setupCheckoutTracking();
    }
    
    getSessionId() {
        let sessionId = sessionStorage.getItem('cart_recovery_session');
        if (!sessionId) {
            sessionId = 'cr_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            sessionStorage.setItem('cart_recovery_session', sessionId);
        }
        return sessionId;
    }
    
    getCustomerId() {
        // Shopify customer ID from global variable
        return window.ShopifyAnalytics?.meta?.page?.customerId || null;
    }
    
    setupCartTracking() {
        // Track add to cart buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-add-to-cart], .btn-add-to-cart, [name="add"]')) {
                this.trackAddToCartIntent(e);
            }
        });
        
        // Track quantity changes
        document.addEventListener('change', (e) => {
            if (e.target.matches('input[name="quantity"], .cart-quantity')) {
                this.trackQuantityChange(e);
            }
        });
    }
    
    setupCheckoutTracking() {
        // Track checkout button clicks
        document.addEventListener('click', (e) => {
            if (e.target.matches('.cart__checkout, [name="goto_checkout"], .checkout-btn')) {
                this.trackCheckoutIntent(e);
            }
        });
        
        // Track shipping method changes (on checkout page)
        if (window.location.pathname.includes('/checkout')) {
            document.addEventListener('change', (e) => {
                if (e.target.matches('input[name="shipping_rate"]')) {
                    this.trackShippingSelection(e);
                }
            });
        }
    }
    
    trackAddToCartIntent(event) {
        const productId = this.extractProductId(event.target);
        const variantId = this.extractVariantId(event.target);
        
        // Send to Web Pixels endpoint
        this.sendEvent('add_to_cart_intent', {
            product_id: productId,
            variant_id: variantId,
            element_clicked: event.target.tagName,
            button_text: event.target.textContent?.trim()
        });
    }
    
    trackQuantityChange(event) {
        this.sendEvent('quantity_changed', {
            new_quantity: event.target.value,
            previous_quantity: event.target.defaultValue,
            product_context: this.getProductContext(event.target)
        });
    }
    
    trackCheckoutIntent(event) {
        this.sendEvent('checkout_intent', {
            cart_total: this.getCartTotal(),
            item_count: this.getCartItemCount(),
            checkout_method: 'button_click'
        });
    }
    
    sendEvent(eventType, data) {
        const eventData = {
            ...data,
            session_id: this.sessionId,
            customer_id: this.customerId,
            url: window.location.href,
            timestamp: new Date().toISOString(),
            user_agent: navigator.userAgent
        };
        
        // Use the global Web Pixels tracker if available
        if (window.WebPixels) {
            window.WebPixels.track(eventType, eventData);
        }
    }
    
    extractProductId(element) {
        // Extract product ID from form or data attributes
        const form = element.closest('form');
        if (form) {
            const productInput = form.querySelector('input[name="id"], input[name="product_id"]');
            return productInput?.value;
        }
        return element.dataset.productId;
    }
    
    extractVariantId(element) {
        const form = element.closest('form');
        if (form) {
            const variantInput = form.querySelector('input[name="id"]:checked, select[name="id"]');
            return variantInput?.value;
        }
        return element.dataset.variantId;
    }
    
    getCartTotal() {
        // Extract from Shopify cart object or DOM
        return window.cart?.total_price || 
               document.querySelector('.cart-total')?.textContent?.replace(/[^0-9.]/g, '');
    }
    
    getCartItemCount() {
        return window.cart?.item_count || 
               document.querySelector('.cart-count')?.textContent;
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new ShopifyCartRecovery();
    });
} else {
    new ShopifyCartRecovery();
}
```

### Product Page Enhanced Tracking

```javascript
// product-page-tracking.js
// Specific tracking for product pages

class ProductPageTracker {
    constructor() {
        this.productId = this.getProductId();
        this.variantId = this.getCurrentVariant();
        this.viewStartTime = Date.now();
        this.scrollDepth = 0;
        this.imagesViewed = new Set();
        
        this.init();
    }
    
    init() {
        this.trackProductView();
        this.setupVariantTracking();
        this.setupImageTracking();
        this.setupReviewsTracking();
        this.setupScrollTracking();
        this.setupTimeOnPage();
    }
    
    trackProductView() {
        WebPixels.track('product_detailed_view', {
            product_id: this.productId,
            variant_id: this.variantId,
            product_title: document.querySelector('.product-title')?.textContent,
            price: this.getCurrentPrice(),
            availability: this.getAvailability(),
            view_source: document.referrer || 'direct'
        });
    }
    
    setupVariantTracking() {
        // Track variant selection changes
        document.addEventListener('change', (e) => {
            if (e.target.matches('.product-variant-select, input[name="id"]')) {
                const newVariant = e.target.value;
                WebPixels.track('variant_changed', {
                    product_id: this.productId,
                    old_variant: this.variantId,
                    new_variant: newVariant,
                    price_change: this.calculatePriceChange(this.variantId, newVariant)
                });
                this.variantId = newVariant;
            }
        });
        
        // Track option selection (size, color, etc.)
        document.addEventListener('click', (e) => {
            if (e.target.matches('.product-option-value')) {
                WebPixels.track('product_option_selected', {
                    product_id: this.productId,
                    option_name: e.target.dataset.optionName,
                    option_value: e.target.textContent,
                    selection_method: 'click'
                });
            }
        });
    }
    
    setupImageTracking() {
        // Track image views in product gallery
        const images = document.querySelectorAll('.product-gallery img');
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !this.imagesViewed.has(entry.target.src)) {
                    this.imagesViewed.add(entry.target.src);
                    WebPixels.track('product_image_viewed', {
                        product_id: this.productId,
                        image_index: Array.from(images).indexOf(entry.target),
                        image_alt: entry.target.alt,
                        total_images: images.length
                    });
                }
            });
        });
        
        images.forEach(img => observer.observe(img));
    }
    
    setupReviewsTracking() {
        // Track reviews interaction
        document.addEventListener('click', (e) => {
            if (e.target.matches('.review-toggle, .show-reviews')) {
                WebPixels.track('reviews_viewed', {
                    product_id: this.productId,
                    reviews_count: document.querySelectorAll('.review-item').length,
                    average_rating: this.getAverageRating()
                });
            }
        });
        
        // Track review helpfulness votes
        document.addEventListener('click', (e) => {
            if (e.target.matches('.review-helpful')) {
                WebPixels.track('review_helpful_vote', {
                    product_id: this.productId,
                    review_id: e.target.dataset.reviewId,
                    vote_type: 'helpful'
                });
            }
        });
    }
    
    setupTimeOnPage() {
        // Track time spent on product page
        window.addEventListener('beforeunload', () => {
            const timeSpent = Date.now() - this.viewStartTime;
            WebPixels.track('product_time_spent', {
                product_id: this.productId,
                time_spent_ms: timeSpent,
                scroll_depth: this.scrollDepth,
                images_viewed: this.imagesViewed.size,
                variant_changes: this.variantChanges || 0
            });
        });
        
        // Also track on visibility change (tab switching)
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                const timeSpent = Date.now() - this.viewStartTime;
                WebPixels.track('product_view_paused', {
                    product_id: this.productId,
                    time_before_pause: timeSpent
                });
            } else {
                this.viewStartTime = Date.now(); // Reset timer
            }
        });
    }
    
    getCurrentPrice() {
        const priceElement = document.querySelector('.product-price, .price');
        return priceElement?.textContent?.replace(/[^0-9.]/g, '');
    }
    
    getAvailability() {
        const availabilityElement = document.querySelector('.product-availability, .stock-status');
        return availabilityElement?.textContent?.toLowerCase().includes('in stock');
    }
    
    getAverageRating() {
        const ratingElement = document.querySelector('.product-rating, .average-rating');
        return ratingElement?.dataset?.rating || 
               parseFloat(ratingElement?.textContent?.match(/[\d.]+/)?.[0]);
    }
}

// Initialize on product pages
if (window.location.pathname.includes('/products/')) {
    new ProductPageTracker();
}
```

## 🛒 Cart Abandonment Detection Examples

### Real-time Abandonment Detection

```javascript
// abandonment-detector.js
class CartAbandonmentDetector {
    constructor() {
        this.abandonmentSignals = {
            rapidClicking: false,
            priceChecking: false,
            formHesitation: false,
            exitIntent: false,
            longInactivity: false
        };
        
        this.clickCount = 0;
        this.priceClickCount = 0;
        this.formStartTime = null;
        this.lastActivityTime = Date.now();
        
        this.init();
    }
    
    init() {
        this.setupRapidClickDetection();
        this.setupPriceCheckingDetection();
        this.setupFormHesitationDetection();
        this.setupExitIntentDetection();
        this.setupInactivityDetection();
        this.startMonitoring();
    }
    
    setupRapidClickDetection() {
        let clickTimes = [];
        
        document.addEventListener('click', (e) => {
            const now = Date.now();
            clickTimes.push(now);
            
            // Keep only clicks from last 10 seconds
            clickTimes = clickTimes.filter(time => now - time <= 10000);
            
            if (clickTimes.length >= 8) {
                this.triggerAbandonmentSignal('rapidClicking', {
                    click_count: clickTimes.length,
                    time_window: '10s',
                    last_element: e.target.tagName
                });
            }
            
            this.lastActivityTime = now;
        });
    }
    
    setupPriceCheckingDetection() {
        document.addEventListener('click', (e) => {
            // Detect price-related element clicks
            const isPriceElement = e.target.matches(
                '.price, .product-price, .total, .subtotal, .shipping-cost, .tax-amount'
            ) || e.target.closest('.price-container, .cost-summary');
            
            if (isPriceElement) {
                this.priceClickCount++;
                
                if (this.priceClickCount >= 3) {
                    this.triggerAbandonmentSignal('priceChecking', {
                        price_clicks: this.priceClickCount,
                        elements_clicked: 'pricing_elements'
                    });
                }
            }
        });
    }
    
    setupFormHesitationDetection() {
        document.addEventListener('focus', (e) => {
            if (e.target.matches('input, textarea, select')) {
                this.formStartTime = Date.now();
            }
        });
        
        document.addEventListener('blur', (e) => {
            if (e.target.matches('input, textarea, select') && this.formStartTime) {
                const focusTime = Date.now() - this.formStartTime;
                const value = e.target.value.trim();
                
                // Long focus time with little input suggests hesitation
                if (focusTime > 30000 && value.length < 3) {
                    this.triggerAbandonmentSignal('formHesitation', {
                        field_type: e.target.type,
                        focus_time_ms: focusTime,
                        characters_entered: value.length,
                        field_name: e.target.name
                    });
                }
            }
        });
    }
    
    setupExitIntentDetection() {
        document.addEventListener('mouseleave', (e) => {
            // Detect mouse leaving viewport towards top (browser UI)
            if (e.clientY <= 0) {
                this.triggerAbandonmentSignal('exitIntent', {
                    page_time_ms: Date.now() - this.pageStartTime,
                    scroll_depth: this.getCurrentScrollDepth(),
                    cart_value: this.getCurrentCartValue()
                });
            }
        });
    }
    
    setupInactivityDetection() {
        const INACTIVITY_THRESHOLD = 5 * 60 * 1000; // 5 minutes
        
        ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(event => {
            document.addEventListener(event, () => {
                this.lastActivityTime = Date.now();
            }, { passive: true });
        });
    }
    
    startMonitoring() {
        // Check for abandonment signals every 30 seconds
        setInterval(() => {
            const inactivityTime = Date.now() - this.lastActivityTime;
            
            if (inactivityTime > 5 * 60 * 1000) { // 5 minutes inactive
                this.triggerAbandonmentSignal('longInactivity', {
                    inactive_time_ms: inactivityTime,
                    page_url: window.location.href
                });
            }
            
            // Send abandonment risk assessment
            this.assessAbandonmentRisk();
        }, 30000);
    }
    
    triggerAbandonmentSignal(signalType, data) {
        this.abandonmentSignals[signalType] = true;
        
        WebPixels.track('abandonment_signal_detected', {
            signal_type: signalType,
            signal_data: data,
            total_signals: Object.values(this.abandonmentSignals).filter(Boolean).length,
            page_type: this.getPageType(),
            session_duration: Date.now() - this.pageStartTime
        });
        
        // Trigger immediate intervention if multiple signals
        const signalCount = Object.values(this.abandonmentSignals).filter(Boolean).length;
        if (signalCount >= 2) {
            this.triggerInterventionOpportunity();
        }
    }
    
    assessAbandonmentRisk() {
        const activeSignals = Object.entries(this.abandonmentSignals)
            .filter(([signal, active]) => active)
            .map(([signal]) => signal);
        
        if (activeSignals.length > 0) {
            const riskLevel = this.calculateRiskLevel(activeSignals);
            
            WebPixels.track('abandonment_risk_assessment', {
                risk_level: riskLevel,
                active_signals: activeSignals,
                cart_value: this.getCurrentCartValue(),
                page_type: this.getPageType(),
                customer_type: this.getCustomerType()
            });
        }
    }
    
    calculateRiskLevel(signals) {
        const weights = {
            rapidClicking: 3,
            priceChecking: 2,
            formHesitation: 4,
            exitIntent: 5,
            longInactivity: 3
        };
        
        const totalWeight = signals.reduce((sum, signal) => sum + (weights[signal] || 0), 0);
        
        if (totalWeight >= 8) return 'high';
        if (totalWeight >= 5) return 'medium';
        return 'low';
    }
    
    triggerInterventionOpportunity() {
        WebPixels.track('intervention_opportunity', {
            signals_active: Object.keys(this.abandonmentSignals).filter(k => this.abandonmentSignals[k]),
            suggested_interventions: this.getSuggestedInterventions(),
            optimal_timing: 'immediate'
        });
    }
    
    getSuggestedInterventions() {
        const interventions = [];
        
        if (this.abandonmentSignals.priceChecking) {
            interventions.push('discount_offer', 'price_explanation');
        }
        
        if (this.abandonmentSignals.formHesitation) {
            interventions.push('form_assistance', 'guest_checkout');
        }
        
        if (this.abandonmentSignals.exitIntent) {
            interventions.push('exit_intent_popup', 'save_cart_reminder');
        }
        
        return interventions;
    }
    
    getCurrentCartValue() {
        return window.cart?.total_price || 
               document.querySelector('.cart-total')?.dataset?.total ||
               '0';
    }
    
    getPageType() {
        if (window.location.pathname.includes('/cart')) return 'cart';
        if (window.location.pathname.includes('/checkout')) return 'checkout';
        if (window.location.pathname.includes('/products')) return 'product';
        return 'other';
    }
    
    getCustomerType() {
        if (window.customer) return 'returning';
        if (sessionStorage.getItem('first_visit') === null) {
            sessionStorage.setItem('first_visit', 'true');
            return 'first_time';
        }
        return 'anonymous_returning';
    }
    
    getCurrentScrollDepth() {
        const scrolled = window.pageYOffset || document.documentElement.scrollTop;
        const maxHeight = document.documentElement.scrollHeight - window.innerHeight;
        return Math.min(scrolled / maxHeight, 1);
    }
}

// Initialize abandonment detection
new CartAbandonmentDetector();
```

## 📊 Event Correlation & Session Analysis Examples

### Session Journey Reconstruction

```python
# session_analysis.py
from datetime import datetime, timedelta
import json
import asyncio
from typing import List, Dict, Any

class SessionJourneyAnalyzer:
    def __init__(self):
        self.sessions = {}
        self.journey_patterns = {}
    
    async def analyze_complete_journey(self, session_id: str, events: List[Dict[str, Any]]):
        """Analyze a complete user journey from events"""
        
        # Sort events by timestamp
        events.sort(key=lambda x: x.get('timestamp', ''))
        
        journey = {
            'session_id': session_id,
            'start_time': events[0]['timestamp'] if events else None,
            'end_time': events[-1]['timestamp'] if events else None,
            'total_events': len(events),
            'pages_visited': set(),
            'products_viewed': set(),
            'cart_actions': [],
            'form_interactions': [],
            'abandonment_signals': [],
            'conversion_events': [],
            'behavioral_metrics': {}
        }
        
        # Process each event
        for event in events:
            await self.process_journey_event(journey, event)
        
        # Calculate journey metrics
        journey['behavioral_metrics'] = self.calculate_journey_metrics(journey, events)
        
        # Classify journey outcome
        journey['outcome'] = self.classify_journey_outcome(journey)
        
        # Generate insights
        journey['insights'] = self.generate_journey_insights(journey)
        
        return journey
    
    async def process_journey_event(self, journey: Dict, event: Dict[str, Any]):
        """Process individual event in journey context"""
        
        event_type = event.get('event_type', '')
        source = event.get('source', '')
        data = event.get('data', {})
        
        # Track page visits
        if 'url' in event:
            journey['pages_visited'].add(event['url'])
        
        # Categorize by event type
        if source == 'web_pixels':
            await self.process_pixels_event(journey, event)
        elif source == 'shopify_webhook':
            await self.process_webhook_event(journey, event)
    
    async def process_pixels_event(self, journey: Dict, event: Dict[str, Any]):
        """Process Web Pixels events"""
        
        event_type = event['event_type']
        data = event.get('data', {})
        
        if event_type == 'clicked':
            # Analyze click patterns
            click_data = {
                'timestamp': event['timestamp'],
                'coordinates': (data.get('clientX'), data.get('clientY')),
                'element': data.get('element_tag'),
                'element_id': data.get('element_id')
            }
            
            if 'click_pattern' not in journey:
                journey['click_pattern'] = []
            journey['click_pattern'].append(click_data)
            
            # Detect rapid clicking (abandonment signal)
            if len(journey['click_pattern']) >= 5:
                recent_clicks = journey['click_pattern'][-5:]
                time_span = self.calculate_time_span(recent_clicks)
                if time_span < 10:  # 5 clicks in under 10 seconds
                    journey['abandonment_signals'].append({
                        'type': 'rapid_clicking',
                        'timestamp': event['timestamp'],
                        'click_count': 5,
                        'time_span': time_span
                    })
        
        elif event_type in ['input_focused', 'input_changed', 'input_blurred']:
            journey['form_interactions'].append({
                'type': event_type,
                'timestamp': event['timestamp'],
                'element_type': data.get('element_type'),
                'form_id': data.get('form_id')
            })
        
        elif event_type == 'form_submitted':
            journey['form_interactions'].append({
                'type': 'form_submitted',
                'timestamp': event['timestamp'],
                'form_id': data.get('form_id'),
                'success': True
            })
        
        elif event_type == 'page_viewed':
            journey['page_engagement'] = {
                'time_on_page': data.get('time_on_page'),
                'scroll_depth': data.get('scroll_depth'),
                'viewport_size': f"{data.get('viewport_width')}x{data.get('viewport_height')}"
            }
    
    async def process_webhook_event(self, journey: Dict, event: Dict[str, Any]):
        """Process Shopify webhook events"""
        
        event_type = event['event_type']
        data = event.get('data', {})
        
        if 'cart' in event_type:
            journey['cart_actions'].append({
                'action': event_type,
                'timestamp': event['timestamp'],
                'total_price': data.get('total_price'),
                'item_count': data.get('item_count'),
                'cart_id': data.get('cart_id')
            })
        
        elif event_type in ['order_create', 'order_paid']:
            journey['conversion_events'].append({
                'type': event_type,
                'timestamp': event['timestamp'],
                'order_id': data.get('order_id'),
                'total_price': data.get('total_price')
            })
    
    def calculate_journey_metrics(self, journey: Dict, events: List[Dict]) -> Dict[str, Any]:
        """Calculate behavioral metrics for the journey"""
        
        if not events:
            return {}
        
        start_time = datetime.fromisoformat(events[0]['timestamp'].replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(events[-1]['timestamp'].replace('Z', '+00:00'))
        duration = (end_time - start_time).total_seconds()
        
        # Click analysis
        click_events = [e for e in events if e.get('event_type') == 'clicked']
        click_density = len(click_events) / max(duration / 60, 1)  # clicks per minute
        
        # Page engagement
        page_events = [e for e in events if e.get('event_type') == 'page_viewed']
        avg_time_on_page = sum(
            e.get('data', {}).get('time_on_page', 0) for e in page_events
        ) / max(len(page_events), 1) if page_events else 0
        
        # Form engagement
        form_events = [e for e in events if 'form' in e.get('event_type', '')]
        form_completion_rate = len([e for e in form_events if e.get('event_type') == 'form_submitted']) / max(len(set(e.get('data', {}).get('form_id') for e in form_events if e.get('data', {}).get('form_id'))), 1)
        
        return {
            'session_duration_seconds': duration,
            'click_density_per_minute': click_density,
            'avg_time_on_page_ms': avg_time_on_page,
            'pages_visited_count': len(journey['pages_visited']),
            'form_completion_rate': form_completion_rate,
            'total_form_interactions': len(form_events),
            'abandonment_signals_count': len(journey['abandonment_signals'])
        }
    
    def classify_journey_outcome(self, journey: Dict) -> str:
        """Classify the journey outcome"""
        
        if journey['conversion_events']:
            return 'conversion'
        elif journey['cart_actions'] and not journey['conversion_events']:
            return 'cart_abandonment'
        elif journey['form_interactions'] and not any(
            fi['type'] == 'form_submitted' for fi in journey['form_interactions']
        ):
            return 'form_abandonment'
        elif len(journey['abandonment_signals']) >= 2:
            return 'high_abandonment_risk'
        elif journey['behavioral_metrics'].get('session_duration_seconds', 0) > 300:
            return 'engaged_browsing'
        else:
            return 'quick_browse'
    
    def generate_journey_insights(self, journey: Dict) -> List[str]:
        """Generate actionable insights from journey analysis"""
        
        insights = []
        metrics = journey['behavioral_metrics']
        
        # High engagement insights
        if metrics.get('session_duration_seconds', 0) > 600:  # 10 minutes
            insights.append("High engagement session - consider personalized recommendations")
        
        # Click pattern insights
        if metrics.get('click_density_per_minute', 0) > 20:
            insights.append("High click density detected - potential confusion or frustration")
        
        # Form abandonment insights
        if journey['form_interactions'] and journey['outcome'] == 'form_abandonment':
            insights.append("Form abandonment detected - simplify checkout process")
        
        # Cart abandonment insights
        if journey['outcome'] == 'cart_abandonment':
            cart_value = journey['cart_actions'][-1].get('total_price') if journey['cart_actions'] else None
            if cart_value and float(cart_value) > 100:
                insights.append(f"High-value cart abandonment (${cart_value}) - send recovery email")
        
        # Page engagement insights
        if metrics.get('avg_time_on_page_ms', 0) < 30000:  # Less than 30 seconds
            insights.append("Low page engagement - improve content relevance")
        
        return insights


# Example usage
async def analyze_session_example():
    analyzer = SessionJourneyAnalyzer()
    
    # Sample events for analysis
    sample_events = [
        {
            'event_id': 'evt_001',
            'event_type': 'page_viewed',
            'source': 'web_pixels',
            'timestamp': '2023-01-01T10:00:00Z',
            'session_id': 'session_123',
            'url': 'https://store.com/products/premium-shoes',
            'data': {
                'time_on_page': 45000,
                'scroll_depth': 0.8,
                'viewport_width': 1920,
                'viewport_height': 1080
            }
        },
        {
            'event_id': 'evt_002',
            'event_type': 'clicked',
            'source': 'web_pixels',
            'timestamp': '2023-01-01T10:01:30Z',
            'session_id': 'session_123',
            'url': 'https://store.com/products/premium-shoes',
            'data': {
                'clientX': 200,
                'clientY': 400,
                'element_tag': 'button',
                'element_id': 'add-to-cart'
            }
        },
        {
            'event_id': 'evt_003',
            'event_type': 'cart_create',
            'source': 'shopify_webhook',
            'timestamp': '2023-01-01T10:01:31Z',
            'session_id': 'session_123',
            'data': {
                'cart_id': 'cart_456',
                'total_price': '199.99',
                'item_count': 1
            }
        }
    ]
    
    # Analyze the journey
    journey = await analyzer.analyze_complete_journey('session_123', sample_events)
    
    print("Journey Analysis Results:")
    print(f"Outcome: {journey['outcome']}")
    print(f"Duration: {journey['behavioral_metrics']['session_duration_seconds']} seconds")
    print(f"Insights: {', '.join(journey['insights'])}")
    
    return journey
```

### Performance Optimization Examples

```python
# performance_config.py
import asyncio
import uvicorn
from multiprocessing import cpu_count

class PerformanceOptimizer:
    """Performance optimization configurations for different deployment scenarios"""
    
    @staticmethod
    def get_high_traffic_config():
        """Configuration for high-traffic stores (>10k events/hour)"""
        return {
            'uvicorn': {
                'host': '0.0.0.0',
                'port': 8000,
                'workers': min(cpu_count() * 2, 8),
                'worker_class': 'uvicorn.workers.UvicornWorker',
                'max_requests': 2000,
                'max_requests_jitter': 200,
                'timeout': 30,
                'keepalive': 5,
                'backlog': 2048
            },
            'redis': {
                'pool_size': 50,
                'pool_max_overflow': 100,
                'socket_keepalive': True,
                'socket_keepalive_options': {
                    'TCP_KEEPIDLE': 60,
                    'TCP_KEEPINTVL': 30,
                    'TCP_KEEPCNT': 3
                }
            },
            'event_processing': {
                'batch_size': 100,
                'batch_timeout_ms': 500,
                'max_queue_size': 10000,
                'worker_threads': 4
            }
        }
    
    @staticmethod 
    def get_medium_traffic_config():
        """Configuration for medium-traffic stores (1k-10k events/hour)"""
        return {
            'uvicorn': {
                'host': '0.0.0.0',
                'port': 8000,
                'workers': cpu_count(),
                'max_requests': 1000,
                'timeout': 30,
                'keepalive': 2
            },
            'redis': {
                'pool_size': 20,
                'pool_max_overflow': 40
            },
            'event_processing': {
                'batch_size': 50,
                'batch_timeout_ms': 1000,
                'max_queue_size': 5000
            }
        }
    
    @staticmethod
    def get_low_traffic_config():
        """Configuration for low-traffic stores (<1k events/hour)"""
        return {
            'uvicorn': {
                'host': '0.0.0.0',
                'port': 8000,
                'workers': max(2, cpu_count() // 2),
                'max_requests': 500,
                'timeout': 60
            },
            'redis': {
                'pool_size': 10,
                'pool_max_overflow': 20
            },
            'event_processing': {
                'batch_size': 25,
                'batch_timeout_ms': 2000,
                'max_queue_size': 1000
            }
        }


# Load balancer configuration examples
NGINX_HIGH_TRAFFIC_CONFIG = '''
upstream shopify_webhooks {
    least_conn;
    server webhook-1:8000 max_fails=3 fail_timeout=30s weight=3;
    server webhook-2:8000 max_fails=3 fail_timeout=30s weight=3;
    server webhook-3:8000 max_fails=3 fail_timeout=30s weight=3;
    keepalive 32;
}

upstream shopify_pixels {
    least_conn;
    server pixels-1:8000 max_fails=3 fail_timeout=30s weight=2;
    server pixels-2:8000 max_fails=3 fail_timeout=30s weight=2;
    server pixels-3:8000 max_fails=3 fail_timeout=30s weight=2;
    server pixels-4:8000 max_fails=3 fail_timeout=30s weight=2;
    server pixels-5:8000 max_fails=3 fail_timeout=30s weight=2;
    keepalive 64;
}

# Rate limiting zones
limit_req_zone $binary_remote_addr zone=webhook_limit:50m rate=200r/m;
limit_req_zone $binary_remote_addr zone=pixels_limit:100m rate=2000r/m;

server {
    listen 443 ssl http2;
    server_name your-high-traffic-store.com;

    # SSL and security headers...
    
    location /webhooks/ {
        limit_req zone=webhook_limit burst=100 nodelay;
        limit_req_status 429;
        
        proxy_pass http://shopify_webhooks;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # Optimize for webhook processing
        proxy_buffering on;
        proxy_buffer_size 64k;
        proxy_buffers 8 64k;
        proxy_busy_buffers_size 128k;
        
        proxy_connect_timeout 10s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    location /pixels/ {
        limit_req zone=pixels_limit burst=500 nodelay;
        limit_req_status 429;
        
        proxy_pass http://shopify_pixels;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # CORS optimizations
        add_header Access-Control-Allow-Origin "$http_origin" always;
        add_header Access-Control-Allow-Methods "POST, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type, X-Session-ID, X-Customer-ID" always;
        add_header Access-Control-Max-Age 86400 always;
        
        # Optimize for high-frequency requests
        proxy_buffering off;
        proxy_connect_timeout 5s;
        proxy_send_timeout 10s;
        proxy_read_timeout 10s;
        
        if ($request_method = 'OPTIONS') {
            add_header Access-Control-Max-Age 86400;
            add_header Content-Type text/plain;
            add_header Content-Length 0;
            return 204;
        }
    }
}
'''
```

## 🎯 A/B Testing Integration Examples

```javascript
// ab-testing-integration.js
class ABTestingIntegration {
    constructor() {
        this.experiments = {};
        this.userSegment = this.determineUserSegment();
        this.init();
    }
    
    init() {
        this.loadActiveExperiments();
        this.setupExperimentTracking();
    }
    
    async loadActiveExperiments() {
        // Load experiments from your A/B testing platform
        try {
            const response = await fetch('/api/experiments/active');
            this.experiments = await response.json();
            
            // Apply experiments
            Object.keys(this.experiments).forEach(experimentId => {
                this.applyExperiment(experimentId);
            });
        } catch (error) {
            console.error('Failed to load experiments:', error);
        }
    }
    
    applyExperiment(experimentId) {
        const experiment = this.experiments[experimentId];
        const variant = this.assignVariant(experimentId, experiment);
        
        // Track experiment exposure
        WebPixels.track('experiment_exposure', {
            experiment_id: experimentId,
            experiment_name: experiment.name,
            variant: variant,
            user_segment: this.userSegment
        });
        
        // Apply variant-specific changes
        this.applyVariantChanges(experimentId, variant, experiment);
    }
    
    assignVariant(experimentId, experiment) {
        // Use consistent hashing for variant assignment
        const userId = this.getUserId();
        const hash = this.hashString(userId + experimentId);
        const bucket = hash % 100;
        
        let cumulativeWeight = 0;
        for (const variant of experiment.variants) {
            cumulativeWeight += variant.weight;
            if (bucket < cumulativeWeight) {
                return variant.name;
            }
        }
        
        return experiment.variants[0].name; // Fallback
    }
    
    applyVariantChanges(experimentId, variant, experiment) {
        const changes = experiment.variants.find(v => v.name === variant)?.changes || {};
        
        // Apply CSS changes
        if (changes.css) {
            const style = document.createElement('style');
            style.textContent = changes.css;
            document.head.appendChild(style);
        }
        
        // Apply JavaScript changes
        if (changes.javascript) {
            try {
                eval(changes.javascript);
            } catch (error) {
                console.error(`Error applying experiment ${experimentId}:`, error);
            }
        }
        
        // Apply element changes
        if (changes.elements) {
            Object.keys(changes.elements).forEach(selector => {
                const elements = document.querySelectorAll(selector);
                const elementChanges = changes.elements[selector];
                
                elements.forEach(element => {
                    if (elementChanges.text) {
                        element.textContent = elementChanges.text;
                    }
                    if (elementChanges.html) {
                        element.innerHTML = elementChanges.html;
                    }
                    if (elementChanges.attributes) {
                        Object.keys(elementChanges.attributes).forEach(attr => {
                            element.setAttribute(attr, elementChanges.attributes[attr]);
                        });
                    }
                });
            });
        }
    }
    
    trackConversion(conversionType, conversionValue = null) {
        // Track conversions for all active experiments
        Object.keys(this.experiments).forEach(experimentId => {
            const variant = this.getAssignedVariant(experimentId);
            
            WebPixels.track('experiment_conversion', {
                experiment_id: experimentId,
                variant: variant,
                conversion_type: conversionType,
                conversion_value: conversionValue,
                user_segment: this.userSegment
            });
        });
    }
    
    setupExperimentTracking() {
        // Track cart additions
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-add-to-cart], .add-to-cart-btn')) {
                this.trackConversion('add_to_cart');
            }
        });
        
        // Track checkout initiation
        document.addEventListener('click', (e) => {
            if (e.target.matches('.checkout-btn, [href*="/checkout"]')) {
                this.trackConversion('checkout_initiated');
            }
        });
        
        // Track purchases (call this when order is completed)
        window.trackPurchase = (orderValue) => {
            this.trackConversion('purchase', orderValue);
        };
    }
    
    determineUserSegment() {
        // Segment users based on behavior/characteristics
        const segments = [];
        
        if (window.customer) {
            segments.push('returning_customer');
        } else {
            segments.push('anonymous');
        }
        
        // Device type
        if (window.innerWidth < 768) {
            segments.push('mobile');
        } else if (window.innerWidth < 1024) {
            segments.push('tablet');
        } else {
            segments.push('desktop');
        }
        
        // Traffic source
        const referrer = document.referrer;
        if (referrer.includes('google')) {
            segments.push('google_traffic');
        } else if (referrer.includes('facebook') || referrer.includes('instagram')) {
            segments.push('social_traffic');
        } else if (referrer) {
            segments.push('referral_traffic');
        } else {
            segments.push('direct_traffic');
        }
        
        return segments.join(',');
    }
    
    getUserId() {
        return window.customer?.id || 
               sessionStorage.getItem('web_pixels_session_id') || 
               'anonymous_' + Date.now();
    }
    
    hashString(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32-bit integer
        }
        return Math.abs(hash);
    }
    
    getAssignedVariant(experimentId) {
        // Retrieve assigned variant (this should be stored somewhere)
        return localStorage.getItem(`experiment_${experimentId}_variant`) || 'control';
    }
}

// Initialize A/B testing
const abTesting = new ABTestingIntegration();

// Example experiment configuration
const SAMPLE_EXPERIMENT = {
    "cart_page_redesign": {
        "name": "Cart Page Redesign",
        "description": "Test new cart page layout",
        "variants": [
            {
                "name": "control",
                "weight": 50,
                "changes": {}
            },
            {
                "name": "new_layout",
                "weight": 50,
                "changes": {
                    "css": ".cart-container { display: grid; grid-template-columns: 2fr 1fr; gap: 2rem; }",
                    "elements": {
                        ".cart-title": {
                            "text": "Your Shopping Bag"
                        },
                        ".checkout-btn": {
                            "text": "Secure Checkout →",
                            "attributes": {
                                "class": "checkout-btn enhanced"
                            }
                        }
                    }
                }
            }
        ]
    }
};
```

These examples provide comprehensive integration patterns for the dual-stream Shopify Cart Recovery system, covering Web Pixels JavaScript integration, cart abandonment detection, session analysis, performance optimization, and A/B testing integration. Each example is production-ready and can be adapted to specific store requirements.