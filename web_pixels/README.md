# Web Pixels Integration Guide

Complete guide for setting up Shopify Web Pixels tracking with the Cart Recovery system for advanced behavioral analytics and cart abandonment detection.

## 🎯 Overview

Web Pixels provides fine-grained tracking of user interactions on your Shopify store, capturing DOM events that traditional webhooks miss:

- **Mouse clicks and coordinates**
- **Form interactions and submissions**
- **Page engagement metrics**
- **Scroll behavior patterns**
- **Session correlation with business events**

## 🚀 Step-by-Step Setup

### Step 1: Access Shopify Admin

1. Log into your Shopify Admin panel
2. Navigate to **Settings** → **Customer events**
3. Click **Add custom pixel**
4. Select **Custom pixel** option

### Step 2: Create the Web Pixel

1. **Name**: `Cart Recovery Analytics`
2. **Description**: `Advanced behavioral tracking for cart recovery`
3. **Data access**: Enable the following permissions:
   - Customer events
   - Checkout events
   - Page view events
   - Product view events

### Step 3: Install the Pixel Code

Copy and paste the entire contents of `web_pixels/pixel.js` into the custom pixel editor:

```javascript
// Update the configuration section
const CONFIG = {
    API_BASE_URL: 'https://YOUR-DOMAIN.com', // ← Update this
    BATCH_SIZE: 10,
    BATCH_TIMEOUT: 2000,
    RETRY_ATTEMPTS: 3,
    // ... rest of config
};
```

### Step 4: Configure Permissions

In the Shopify pixel configuration, ensure these data access permissions are enabled:

- ✅ **Customer events**: For customer identification
- ✅ **Checkout events**: For checkout correlation
- ✅ **Page view events**: For engagement tracking
- ✅ **Product view events**: For product interaction analysis

### Step 5: Publish and Test

1. Click **Save** to create the pixel
2. Click **Publish** to activate on your store
3. Test using the verification steps below

## 🔧 Configuration Options

### Basic Configuration

```javascript
const CONFIG = {
    // Your backend API endpoint
    API_BASE_URL: 'https://your-domain.com',
    
    // Event batching settings
    BATCH_SIZE: 10,           // Events per batch
    BATCH_TIMEOUT: 2000,      // Max wait time (ms)
    
    // Retry configuration
    RETRY_ATTEMPTS: 3,        // Max retry attempts
    RETRY_DELAY: 1000,        // Delay between retries (ms)
    
    // Performance settings
    THROTTLE_DELAY: 100,      // Event throttling (ms)
    SESSION_TIMEOUT: 1800000, // 30 minutes
    
    // Privacy settings
    PRIVACY_CONSENT_KEY: 'shopify_pixels_consent'
};
```

### Advanced Configuration

```javascript
// Custom event filtering
const TRACKED_ELEMENTS = {
    buttons: ['add-to-cart', 'checkout-btn', 'buy-now'],
    forms: ['newsletter', 'contact', 'checkout'],
    links: ['product-link', 'collection-link']
};

// Enhanced tracking options
const TRACKING_OPTIONS = {
    mouseMovement: true,       // Track mouse movements
    scrollBehavior: true,      // Track scroll patterns
    formAnalytics: true,       // Detailed form analytics
    pageEngagement: true,      // Time on page, scroll depth
    clickPatterns: true        // Click density analysis
};
```

## 📊 Event Schema Reference

### Click Events

```json
{
  "event_type": "clicked",
  "data": {
    "clientX": 150,              // Mouse X coordinate
    "clientY": 250,              // Mouse Y coordinate
    "element_id": "add-to-cart", // Element ID
    "element_class": "btn btn-primary", // CSS classes
    "element_tag": "button",     // HTML tag
    "element_text": "Add to Cart", // Button/link text
    "element_href": "/cart",     // Link href (if applicable)
    "target_selector": "button#add-to-cart", // CSS selector
    "page_x": 150,               // Page X coordinate
    "page_y": 350,               // Page Y coordinate
    "url": "https://store.com/products/item"
  },
  "session_id": "wp_123_abc",
  "customer_id": "555555",
  "timestamp": "2023-01-01T12:00:00Z"
}
```

### Form Interaction Events

```json
{
  "event_type": "input_changed",
  "data": {
    "element_id": "email-input",
    "element_name": "email",
    "element_type": "email",
    "element_value": "user@example.com",
    "previous_value": "",
    "element_selector": "input#email-input",
    "form_id": "newsletter-form",
    "url": "https://store.com/pages/contact"
  },
  "session_id": "wp_123_abc",
  "customer_id": "555555",
  "timestamp": "2023-01-01T12:01:00Z"
}
```

### Page Engagement Events

```json
{
  "event_type": "page_viewed",
  "data": {
    "page_title": "Premium Product | Store",
    "referrer": "https://google.com",
    "page_type": "product",
    "viewport_width": 1920,
    "viewport_height": 1080,
    "screen_width": 1920,
    "screen_height": 1080,
    "scroll_depth": 0.75,       // 75% of page scrolled
    "time_on_page": 45000,      // 45 seconds
    "url": "https://store.com/products/premium-item"
  },
  "session_id": "wp_123_abc",
  "timestamp": "2023-01-01T12:00:00Z"
}
```

## 🔗 Session Correlation

### How Session Tracking Works

1. **Session Generation**: Unique session ID created on first page load
2. **Cross-Page Persistence**: Session ID stored in `sessionStorage`
3. **Customer Linking**: Automatic detection of Shopify customer ID
4. **Event Correlation**: All events tagged with session and customer IDs

### Session ID Format

```javascript
// Format: wp_<timestamp>_<random>
// Example: wp_1672531200000_a1b2c3d4e
const sessionId = 'wp_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
```

### Customer Identification

```javascript
// Automatic detection from Shopify globals
if (window.Shopify?.customerID) {
    this.customerId = window.Shopify.customerID.toString();
} else if (window.__st?.cid) {
    this.customerId = window.__st.cid.toString();
}
```

## 🔒 Privacy & Compliance

### GDPR Compliance

The Web Pixel respects user privacy and GDPR requirements:

```javascript
// Check user consent
hasConsent() {
    try {
        const consent = localStorage.getItem('shopify_pixels_consent');
        return consent === 'true' || !consent; // Default to true
    } catch (e) {
        return true; // Fallback for privacy mode
    }
}

// Opt-out functionality
optOut() {
    localStorage.setItem('shopify_pixels_consent', 'false');
    this.eventQueue = [];
    sessionStorage.removeItem('web_pixels_session_id');
}
```

### Data Minimization

- **Text Truncation**: Element text limited to 100 characters
- **Sensitive Data Filtering**: No passwords or credit card data
- **Selective Tracking**: Only essential interaction data collected
- **Consent Respect**: Stops tracking when consent withdrawn

### Cookie-Free Tracking

Web Pixels uses `sessionStorage` instead of cookies:

```javascript
// Session storage (not cookies)
sessionStorage.setItem('web_pixels_session_id', sessionId);

// No persistent cross-site tracking
// Session ends when browser tab closes
```

## 🧪 Testing & Validation

### Test Installation

1. **Open Browser Dev Tools**
2. **Navigate to your Shopify store**
3. **Check Console**: Look for Web Pixels initialization logs
4. **Network Tab**: Monitor HTTP requests to your API endpoint

### Validation Checklist

- [ ] Console shows "Web Pixels Tracker initialized"
- [ ] Click events generate network requests
- [ ] Form interactions are tracked
- [ ] Session ID remains consistent across pages
- [ ] Customer ID detected when logged in

### Test Commands

```bash
# Monitor incoming events
curl -X GET http://localhost:8002/metrics

# Check service health
curl -X GET http://localhost:8002/health

# Test specific endpoints
curl -X POST http://localhost:8002/pixels/clicked \
  -H "Content-Type: application/json" \
  -d '{"clientX": 100, "clientY": 200, "element_tag": "button", "url": "https://test.com"}'
```

## 🐛 Debugging

### Common Issues

#### 1. Events Not Reaching Backend

**Symptoms**: No events in backend logs, metrics show zero events

**Solutions**:
```javascript
// Check API endpoint configuration
console.log('API_BASE_URL:', CONFIG.API_BASE_URL);

// Verify CORS headers
// Network tab should show successful POST requests

// Check for JavaScript errors
window.addEventListener('error', (e) => {
    console.error('Pixel error:', e);
});
```

#### 2. Session Not Persisting

**Symptoms**: New session ID on each page load

**Solutions**:
```javascript
// Check sessionStorage availability
if (typeof Storage !== "undefined") {
    console.log("sessionStorage available");
} else {
    console.error("sessionStorage not supported");
}

// Verify session storage manually
console.log("Session ID:", sessionStorage.getItem('web_pixels_session_id'));
```

#### 3. Customer ID Not Detected

**Symptoms**: Events show null customer_id

**Solutions**:
```javascript
// Debug customer detection
console.log('Shopify.customerID:', window.Shopify?.customerID);
console.log('__st.cid:', window.__st?.cid);

// Manual customer ID setting
WebPixels.setCustomer('123456');
```

### Debug Mode

Enable debug logging by adding to pixel code:

```javascript
const DEBUG = true;

if (DEBUG) {
    console.log('Web Pixels Debug Mode Enabled');
    
    // Log all events before sending
    this.queueEvent = function(eventType, eventData) {
        console.log('Queuing event:', eventType, eventData);
        // ... original implementation
    };
}
```

### Browser Console Testing

```javascript
// Test pixel functionality directly
WebPixels.track('test_event', { test: true });

// Check session info
console.log('Session ID:', window.WebPixelsTracker?.sessionId);
console.log('Customer ID:', window.WebPixelsTracker?.customerId);

// Manual event trigger
window.WebPixelsTracker?.queueEvent('clicked', {
    clientX: 100,
    clientY: 200,
    element_tag: 'button',
    url: window.location.href
});
```

## 🔧 Advanced Configuration

### Custom Event Tracking

```javascript
// Add custom business events
WebPixels.track('product_comparison', {
    products: ['product_1', 'product_2'],
    comparison_type: 'features'
});

WebPixels.track('wishlist_add', {
    product_id: '12345',
    variant_id: '67890'
});
```

### Performance Optimization

```javascript
// High-traffic store configuration
const CONFIG = {
    BATCH_SIZE: 20,           // Larger batches
    BATCH_TIMEOUT: 1000,      // Faster sends
    THROTTLE_DELAY: 200,      // Less aggressive throttling
    MAX_QUEUE_SIZE: 100       // Prevent memory issues
};

// Selective tracking for performance
const PERFORMANCE_MODE = {
    trackMouseMovement: false,  // Disable for high traffic
    trackScrolling: true,       // Keep engagement metrics
    trackFormInteractions: true, // Keep conversion insights
    throttleClicks: true        // Reduce click frequency
};
```

### A/B Testing Support

```javascript
// Include experiment data in events
const getExperimentData = () => ({
    experiment_id: window.shopifyExperiment?.id,
    variant: window.shopifyExperiment?.variant,
    segment: window.customerSegment
});

// Add to all events
eventData.experiment_data = getExperimentData();
```

## 📈 Analytics Integration

### Google Analytics 4

```javascript
// Send key events to GA4
const sendToGA4 = (eventName, eventData) => {
    if (typeof gtag !== 'undefined') {
        gtag('event', eventName, {
            session_id: eventData.session_id,
            customer_id: eventData.customer_id,
            custom_parameters: eventData.data
        });
    }
};

// Integration example
this.queueEvent = function(eventType, eventData) {
    // Send to Cart Recovery system
    originalQueueEvent.call(this, eventType, eventData);
    
    // Also send to GA4
    if (eventType === 'form_submitted') {
        sendToGA4('form_submit', eventData);
    }
};
```

### Custom Analytics Dashboard

```javascript
// Real-time analytics endpoint
const ANALYTICS_ENDPOINT = 'https://your-domain.com/analytics/realtime';

// Send summary metrics
setInterval(() => {
    const metrics = {
        session_id: this.sessionId,
        events_sent: this.eventsSent,
        page_views: this.pageViews,
        click_count: this.clickCount,
        form_interactions: this.formInteractions
    };
    
    fetch(ANALYTICS_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(metrics)
    });
}, 30000); // Every 30 seconds
```

## 🎯 Business Use Cases

### Cart Recovery Optimization

```javascript
// Detect cart abandonment signals
const detectAbandonmentRisk = () => {
    const signals = {
        rapid_clicking: this.clickCount > 10 && this.sessionDuration < 60000,
        form_abandonment: this.formStarted && !this.formSubmitted,
        price_checking: this.priceClicks > 3,
        comparison_shopping: this.productViews > 5
    };
    
    if (Object.values(signals).some(signal => signal)) {
        WebPixels.track('abandonment_risk', { signals });
    }
};
```

### Personalization Triggers

```javascript
// Identify high-intent visitors
const analyzeIntent = () => {
    const intentScore = 
        (this.timeOnPage > 120000 ? 20 : 0) +      // 2+ minutes
        (this.scrollDepth > 0.8 ? 15 : 0) +        // 80%+ scroll
        (this.productClicks > 2 ? 25 : 0) +        // Multiple clicks
        (this.formInteractions > 0 ? 30 : 0);      // Form engagement
    
    if (intentScore > 50) {
        WebPixels.track('high_intent_visitor', { 
            score: intentScore,
            session_id: this.sessionId
        });
    }
};
```

### UX Optimization

```javascript
// Track friction points
const trackFriction = () => {
    if (this.rapidClicks > 5) {
        WebPixels.track('ux_friction', {
            type: 'rapid_clicking',
            element: this.lastClickedElement,
            coordinates: [this.lastClickX, this.lastClickY]
        });
    }
    
    if (this.formErrors > 0) {
        WebPixels.track('ux_friction', {
            type: 'form_errors',
            form_id: this.currentFormId,
            error_count: this.formErrors
        });
    }
};
```

---

## 📚 Additional Resources

- **API Documentation**: Full endpoint documentation at `/docs`
- **Event Processing Guide**: See main README.md
- **Troubleshooting**: Common issues and solutions
- **Performance Tuning**: Optimization for high-traffic stores

## 🆘 Support

For Web Pixels specific issues:

1. **Check Browser Console**: Look for JavaScript errors
2. **Monitor Network Tab**: Verify API requests are being sent
3. **Test Endpoints**: Use curl to test backend connectivity
4. **Review Logs**: Check backend service logs for event processing

**Need help?** Open a GitHub issue with:
- Browser and version
- Shopify store URL (if shareable)
- Console error messages
- Network request screenshots