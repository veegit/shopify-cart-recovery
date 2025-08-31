// Shopify Web Pixels Extension for Cart Recovery
(function() {
    'use strict';
    
    const CONFIG = {
        API_BASE_URL: window.WEB_PIXELS_ENDPOINT || 'https://your-app-domain.com',
        BATCH_SIZE: 10,
        BATCH_TIMEOUT: 2000,
        RETRY_ATTEMPTS: 3,
        RETRY_DELAY: 1000,
        THROTTLE_DELAY: 100,
        SESSION_TIMEOUT: 30 * 60 * 1000, // 30 minutes
        PRIVACY_CONSENT_KEY: 'shopify_pixels_consent'
    };
    
    class WebPixelsTracker {
        constructor() {
            this.sessionId = this.getOrCreateSessionId();
            this.customerId = null;
            this.shopDomain = window.Shopify?.shop || null;
            this.eventQueue = [];
            this.isProcessing = false;
            this.sequenceNumber = 0;
            this.pageStartTime = Date.now();
            this.scrollDepth = 0;
            this.lastMouseEvent = 0;
            this.retryQueue = [];
            
            this.init();
        }
        
        init() {
            if (!this.hasConsent()) {
                console.log('Web Pixels: User consent not given');
                return;
            }
            
            this.setupEventListeners();
            this.setupBatchProcessor();
            this.trackPageView();
            this.detectCustomer();
        }
        
        hasConsent() {
            try {
                const consent = localStorage.getItem(CONFIG.PRIVACY_CONSENT_KEY);
                return consent === 'true' || !consent; // Default to true if not set
            } catch (e) {
                return true; // Fallback for privacy mode browsers
            }
        }
        
        getOrCreateSessionId() {
            try {
                let sessionId = sessionStorage.getItem('web_pixels_session_id');
                if (!sessionId) {
                    sessionId = 'wp_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
                    sessionStorage.setItem('web_pixels_session_id', sessionId);
                }
                return sessionId;
            } catch (e) {
                return 'wp_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            }
        }
        
        detectCustomer() {
            if (window.Shopify?.customerID) {
                this.customerId = window.Shopify.customerID.toString();
            } else if (window.__st?.cid) {
                this.customerId = window.__st.cid.toString();
            }
        }
        
        setupEventListeners() {
            this.setupClickTracking();
            this.setupFormTracking();
            this.setupScrollTracking();
            this.setupMouseTracking();
            this.setupPageEngagement();
        }
        
        setupClickTracking() {
            document.addEventListener('click', (event) => {
                const elementData = this.extractElementData(event.target);
                
                this.queueEvent('clicked', {
                    clientX: event.clientX,
                    clientY: event.clientY,
                    pageX: event.pageX,
                    pageY: event.pageY,
                    element_id: elementData.id,
                    element_class: elementData.className,
                    element_tag: elementData.tagName,
                    element_href: elementData.href,
                    element_text: elementData.text,
                    element_value: elementData.value,
                    target_selector: this.generateSelector(event.target),
                    url: window.location.href
                });
            }, true);
        }
        
        setupFormTracking() {
            document.addEventListener('focus', (event) => {
                if (this.isFormElement(event.target)) {
                    const elementData = this.extractElementData(event.target);
                    
                    this.queueEvent('input_focused', {
                        element_id: elementData.id,
                        element_name: elementData.name,
                        element_type: elementData.type,
                        element_selector: this.generateSelector(event.target),
                        form_id: this.getFormId(event.target),
                        focus_timestamp: new Date().toISOString(),
                        url: window.location.href
                    });
                    
                    event.target._focusTime = Date.now();
                }
            }, true);
            
            document.addEventListener('blur', (event) => {
                if (this.isFormElement(event.target)) {
                    const elementData = this.extractElementData(event.target);
                    const focusDuration = event.target._focusTime ? 
                        Date.now() - event.target._focusTime : null;
                    
                    this.queueEvent('input_blurred', {
                        element_id: elementData.id,
                        element_name: elementData.name,
                        element_type: elementData.type,
                        element_selector: this.generateSelector(event.target),
                        form_id: this.getFormId(event.target),
                        blur_timestamp: new Date().toISOString(),
                        focus_duration: focusDuration,
                        url: window.location.href
                    });
                }
            }, true);
            
            document.addEventListener('input', this.throttle((event) => {
                if (this.isFormElement(event.target)) {
                    const elementData = this.extractElementData(event.target);
                    
                    this.queueEvent('input_changed', {
                        element_id: elementData.id,
                        element_name: elementData.name,
                        element_type: elementData.type,
                        element_value: elementData.value,
                        previous_value: event.target._previousValue || '',
                        element_selector: this.generateSelector(event.target),
                        form_id: this.getFormId(event.target),
                        url: window.location.href
                    });
                    
                    event.target._previousValue = elementData.value;
                }
            }, CONFIG.THROTTLE_DELAY), true);
            
            document.addEventListener('submit', (event) => {
                if (event.target.tagName === 'FORM') {
                    const formData = this.extractFormData(event.target);
                    
                    this.queueEvent('form_submitted', {
                        form_id: formData.id,
                        form_name: formData.name,
                        form_action: formData.action,
                        form_method: formData.method,
                        field_count: formData.fieldCount,
                        filled_fields: formData.filledFields,
                        form_selector: this.generateSelector(event.target),
                        submission_method: 'submit',
                        url: window.location.href
                    });
                }
            }, true);
        }
        
        setupScrollTracking() {
            let lastScrollTime = 0;
            
            window.addEventListener('scroll', this.throttle(() => {
                const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                const documentHeight = Math.max(
                    document.body.scrollHeight,
                    document.documentElement.scrollHeight
                );
                const windowHeight = window.innerHeight;
                
                this.scrollDepth = Math.max(
                    this.scrollDepth,
                    (scrollTop + windowHeight) / documentHeight
                );
                
                lastScrollTime = Date.now();
            }, 500));
        }
        
        setupMouseTracking() {
            document.addEventListener('mousemove', this.throttle((event) => {
                this.lastMouseEvent = Date.now();
            }, 1000));
        }
        
        setupPageEngagement() {
            const trackPageView = () => {
                this.queueEvent('page_viewed', {
                    page_title: document.title,
                    referrer: document.referrer,
                    page_type: this.getPageType(),
                    viewport_width: window.innerWidth,
                    viewport_height: window.innerHeight,
                    screen_width: screen.width,
                    screen_height: screen.height,
                    scroll_depth: this.scrollDepth,
                    time_on_page: Date.now() - this.pageStartTime,
                    url: window.location.href
                });
            };
            
            window.addEventListener('beforeunload', trackPageView);
            
            // Track page view on visibility change (tab switching)
            document.addEventListener('visibilitychange', () => {
                if (document.hidden) {
                    trackPageView();
                }
            });
        }
        
        trackPageView() {
            this.queueEvent('page_viewed', {
                page_title: document.title,
                referrer: document.referrer,
                page_type: this.getPageType(),
                viewport_width: window.innerWidth,
                viewport_height: window.innerHeight,
                screen_width: screen.width,
                screen_height: screen.height,
                scroll_depth: 0,
                time_on_page: 0,
                url: window.location.href
            });
        }
        
        extractElementData(element) {
            return {
                id: element.id || null,
                name: element.name || null,
                className: element.className || null,
                tagName: element.tagName?.toLowerCase() || null,
                type: element.type || null,
                href: element.href || null,
                text: element.textContent?.trim().substring(0, 100) || null,
                value: element.value || null
            };
        }
        
        extractFormData(form) {
            const inputs = form.querySelectorAll('input, select, textarea');
            const filledFields = Array.from(inputs).filter(input => 
                input.value && input.value.trim() !== ''
            ).length;
            
            return {
                id: form.id || null,
                name: form.name || null,
                action: form.action || null,
                method: form.method || 'POST',
                fieldCount: inputs.length,
                filledFields: filledFields
            };
        }
        
        isFormElement(element) {
            const formTags = ['input', 'select', 'textarea'];
            return formTags.includes(element.tagName?.toLowerCase());
        }
        
        getFormId(element) {
            const form = element.closest('form');
            return form ? (form.id || form.name || null) : null;
        }
        
        generateSelector(element) {
            if (element.id) return `#${element.id}`;
            if (element.className) {
                const classes = element.className.split(' ').filter(c => c).slice(0, 2);
                if (classes.length) return `${element.tagName?.toLowerCase()}.${classes.join('.')}`;
            }
            return element.tagName?.toLowerCase() || null;
        }
        
        getPageType() {
            const path = window.location.pathname;
            if (path.includes('/cart')) return 'cart';
            if (path.includes('/checkout')) return 'checkout';
            if (path.includes('/products/')) return 'product';
            if (path.includes('/collections/')) return 'collection';
            if (path === '/') return 'home';
            return 'other';
        }
        
        queueEvent(eventType, eventData) {
            if (!this.hasConsent()) return;
            
            const event = {
                ...eventData,
                session_id: this.sessionId,
                customer_id: this.customerId,
                shop_domain: this.shopDomain,
                user_agent: navigator.userAgent,
                sequence_number: ++this.sequenceNumber,
                timestamp: new Date().toISOString()
            };
            
            this.eventQueue.push({ type: eventType, data: event });
            
            if (this.eventQueue.length >= CONFIG.BATCH_SIZE) {
                this.processBatch();
            }
        }
        
        setupBatchProcessor() {
            setInterval(() => {
                if (this.eventQueue.length > 0) {
                    this.processBatch();
                }
            }, CONFIG.BATCH_TIMEOUT);
        }
        
        async processBatch() {
            if (this.isProcessing || this.eventQueue.length === 0) return;
            
            this.isProcessing = true;
            const batch = this.eventQueue.splice(0, CONFIG.BATCH_SIZE);
            
            for (const event of batch) {
                try {
                    await this.sendEvent(event.type, event.data);
                } catch (error) {
                    this.retryQueue.push({ ...event, attempts: 1 });
                }
            }
            
            await this.processRetryQueue();
            this.isProcessing = false;
        }
        
        async sendEvent(eventType, eventData, attempt = 1) {
            const endpoint = `${CONFIG.API_BASE_URL}/pixels/${eventType}`;
            
            const headers = {
                'Content-Type': 'application/json'
            };
            
            if (this.customerId) {
                headers['X-Customer-ID'] = this.customerId;
            }
            
            if (this.sessionId) {
                headers['X-Session-ID'] = this.sessionId;
            }
            
            if (this.shopDomain) {
                headers['X-Shop-Domain'] = this.shopDomain;
            }
            
            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: headers,
                    body: JSON.stringify(eventData),
                    signal: AbortSignal.timeout(5000)
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                return await response.json();
                
            } catch (error) {
                console.warn(`Web Pixels: Failed to send ${eventType} event (attempt ${attempt}):`, error.message);
                
                if (attempt < CONFIG.RETRY_ATTEMPTS && !error.name === 'AbortError') {
                    await this.delay(CONFIG.RETRY_DELAY * attempt);
                    return this.sendEvent(eventType, eventData, attempt + 1);
                }
                
                throw error;
            }
        }
        
        async processRetryQueue() {
            const retryBatch = this.retryQueue.splice(0, 5);
            
            for (const item of retryBatch) {
                if (item.attempts < CONFIG.RETRY_ATTEMPTS) {
                    try {
                        await this.sendEvent(item.type, item.data, item.attempts + 1);
                    } catch (error) {
                        item.attempts++;
                        if (item.attempts < CONFIG.RETRY_ATTEMPTS) {
                            this.retryQueue.push(item);
                        }
                    }
                }
            }
        }
        
        throttle(func, delay) {
            let timeoutId;
            let lastExecTime = 0;
            
            return function(...args) {
                const currentTime = Date.now();
                
                if (currentTime - lastExecTime > delay) {
                    func.apply(this, args);
                    lastExecTime = currentTime;
                } else {
                    clearTimeout(timeoutId);
                    timeoutId = setTimeout(() => {
                        func.apply(this, args);
                        lastExecTime = Date.now();
                    }, delay - (currentTime - lastExecTime));
                }
            };
        }
        
        delay(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        }
        
        handleError(error, context) {
            console.error('Web Pixels Error:', error, context);
            
            // Don't track errors for privacy violations or consent issues
            if (error.message?.includes('consent') || error.message?.includes('privacy')) {
                return;
            }
            
            try {
                this.queueEvent('error', {
                    error_message: error.message,
                    error_context: context,
                    url: window.location.href,
                    user_agent: navigator.userAgent
                });
            } catch (e) {
                // Fail silently if we can't even queue the error
            }
        }
        
        // Public methods for manual tracking
        trackCustomEvent(eventType, customData) {
            if (!this.hasConsent()) return;
            
            this.queueEvent('custom', {
                custom_event_type: eventType,
                custom_data: customData,
                url: window.location.href
            });
        }
        
        setCustomerId(customerId) {
            this.customerId = customerId?.toString() || null;
        }
        
        // Privacy compliance methods
        optOut() {
            try {
                localStorage.setItem(CONFIG.PRIVACY_CONSENT_KEY, 'false');
                this.eventQueue = [];
                this.retryQueue = [];
                sessionStorage.removeItem('web_pixels_session_id');
            } catch (e) {
                console.warn('Web Pixels: Could not opt out');
            }
        }
        
        optIn() {
            try {
                localStorage.setItem(CONFIG.PRIVACY_CONSENT_KEY, 'true');
                this.init();
            } catch (e) {
                console.warn('Web Pixels: Could not opt in');
            }
        }
    }
    
    // Initialize the tracker when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.WebPixelsTracker = new WebPixelsTracker();
        });
    } else {
        window.WebPixelsTracker = new WebPixelsTracker();
    }
    
    // Expose global methods for Shopify integration
    window.WebPixels = {
        track: (eventType, data) => window.WebPixelsTracker?.trackCustomEvent(eventType, data),
        setCustomer: (customerId) => window.WebPixelsTracker?.setCustomerId(customerId),
        optOut: () => window.WebPixelsTracker?.optOut(),
        optIn: () => window.WebPixelsTracker?.optIn()
    };
    
})();

// Shopify Web Pixels API Integration
if (typeof analytics !== 'undefined' && analytics.subscribe) {
    
    // Subscribe to Shopify's built-in events
    analytics.subscribe('page_viewed', (event) => {
        if (window.WebPixelsTracker) {
            window.WebPixelsTracker.queueEvent('page_viewed', {
                page_title: event.context?.document?.title,
                referrer: event.context?.document?.referrer,
                url: event.context?.document?.location?.href,
                viewport_width: event.context?.window?.innerWidth,
                viewport_height: event.context?.window?.innerHeight,
                time_on_page: 0,
                scroll_depth: 0
            });
        }
    });
    
    analytics.subscribe('product_viewed', (event) => {
        if (window.WebPixelsTracker) {
            window.WebPixelsTracker.trackCustomEvent('product_viewed', {
                product_id: event.data?.productVariant?.product?.id,
                variant_id: event.data?.productVariant?.id,
                product_title: event.data?.productVariant?.product?.title,
                price: event.data?.productVariant?.price?.amount
            });
        }
    });
    
    analytics.subscribe('cart_viewed', (event) => {
        if (window.WebPixelsTracker) {
            window.WebPixelsTracker.trackCustomEvent('cart_viewed', {
                cart_total: event.data?.cart?.cost?.totalAmount?.amount,
                item_count: event.data?.cart?.lines?.length
            });
        }
    });
    
    analytics.subscribe('checkout_started', (event) => {
        if (window.WebPixelsTracker) {
            window.WebPixelsTracker.trackCustomEvent('checkout_started', {
                checkout_total: event.data?.checkout?.totalPrice?.amount,
                item_count: event.data?.checkout?.lineItems?.length
            });
        }
    });
    
    analytics.subscribe('payment_info_submitted', (event) => {
        if (window.WebPixelsTracker) {
            window.WebPixelsTracker.trackCustomEvent('payment_info_submitted', {
                checkout_total: event.data?.checkout?.totalPrice?.amount
            });
        }
    });
    
}