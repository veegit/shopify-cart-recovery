# Claude Code Prompts - MVP Part 1 Development Plan

## Overview
MVP Part 1 focuses on dual Shopify integration: traditional webhooks AND Web Pixels API for fine-grained user interaction tracking. Events from both streams flow to Redis PubSub with structured logging. The entire system will be containerized with Docker Compose for easy development and deployment.

## Data Collection Streams
1. **Shopify Webhooks**: Cart updates, orders, checkouts (server-to-server)
2. **Web Pixels API**: Clicks, mouse movements, form interactions, DOM events (client-side)
3. **Combined Processing**: Correlate webhook events with user behavior patterns

## Project Structure
```
shopify-cart-recovery/
├── docker-compose.yml
├── requirements.txt
├── Dockerfile
├── .env.example
├── .gitignore
├── README.md
├── apps/
│   ├── __init__.py
│   ├── shopify_webhook_handler/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── models.py
│   ├── web_pixels_handler/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── models.py
│   ├── event_processor/
│   │   ├── __init__.py
│   │   └── main.py
│   └── shared/
│       ├── __init__.py
│       ├── redis_client.py
│       ├── config.py
│       └── logging_config.py
├── web_pixels/
│   ├── pixel.js
│   └── README.md
└── tests/
    ├── __init__.py
    ├── test_webhook_handler.py
    ├── test_web_pixels_handler.py
    └── test_event_processor.py
```

## Development Phases & Claude Code Prompts

### Phase 1.1: Project Foundation (Day 1-2)

#### Prompt 1: Project Setup and Configuration
```
Create a Python project structure for a Shopify cart recovery app with the following requirements:

1. Create a docker-compose.yml file that includes:
   - Redis container with pub/sub enabled
   - Python app container
   - Environment variable support
   - Development volume mounts

2. Create a Dockerfile for the Python application that:
   - Uses Python 3.11 slim base image
   - Installs requirements from requirements.txt
   - Sets up proper working directory
   - Runs the application

3. Create requirements.txt with:
   - FastAPI for web framework
   - redis-py for Redis connection
   - pydantic for data validation
   - python-dotenv for environment variables
   - uvicorn for ASGI server
   - requests for HTTP calls
   - pytest for testing

4. Create .env.example with:
   - Redis connection settings
   - Shopify API credentials placeholder
   - Logging configuration
   - App port settings

5. Create a shared configuration module (apps/shared/config.py) that:
   - Loads environment variables
   - Validates required settings
   - Provides configuration classes for different components

Include proper .gitignore for Python projects.
```

#### Prompt 2: Logging and Redis Client Setup
```
Create shared utility modules for the Shopify cart recovery app:

1. Create apps/shared/logging_config.py that:
   - Sets up structured logging with JSON format
   - Includes timestamp, log level, component name, and message
   - Configures different log levels for development vs production
   - Provides logger instances for different app components

2. Create apps/shared/redis_client.py that:
   - Establishes Redis connection with connection pooling
   - Provides pub/sub publisher and subscriber classes
   - Includes error handling and retry logic
   - Supports both publishing and subscribing to channels
   - Has methods for:
     * publish_event(channel, event_data)
     * subscribe_to_events(channels, callback)
     * health_check()

3. Include proper error handling, connection recovery, and logging throughout both modules.

Use the configuration from apps/shared/config.py for all settings.
```

### Phase 1.2: Shopify Integration (Day 3-4)

#### Prompt 3: Web Pixels Handler and Models
```
Create Web Pixels event handling in apps/web_pixels_handler/:

1. Create models.py with Pydantic models for Web Pixels events:
   - ClickedEventModel: Handle clicked DOM events with mouse coordinates, element details
   - InputChangedEventModel: Handle form input changes 
   - InputFocusedEventModel: Handle input focus events
   - InputBlurredEventModel: Handle input blur events
   - FormSubmittedEventModel: Handle form submission events
   - PageViewedEventModel: Handle page view events from pixels

2. Each model should include:
   - All Web Pixels API event properties (clientX, clientY, element details, etc.)
   - Session correlation fields (session_id, customer_id)
   - Timestamp and event sequence handling
   - Method to convert to standardized Redis event format

3. Create a WebPixelEventProcessor class that:
   - Validates incoming Web Pixels payloads
   - Enriches events with session context
   - Handles event correlation and deduplication
   - Converts to standardized format for Redis publishing

Include comprehensive validation for mouse coordinates, element properties, and event sequencing.
```

#### Prompt 4: Web Pixels HTTP Handler Service
```
Create the Web Pixels handler service in apps/web_pixels_handler/main.py:

1. Create a FastAPI application with endpoints for Web Pixels data:
   - POST /pixels/clicked - Handle click events
   - POST /pixels/input_changed - Handle input change events  
   - POST /pixels/input_focused - Handle input focus events
   - POST /pixels/input_blurred - Handle input blur events
   - POST /pixels/form_submitted - Handle form submission events
   - POST /pixels/page_viewed - Handle page view events

2. Each endpoint should:
   - Accept JSON payload from Web Pixels JavaScript
   - Validate against appropriate Pydantic model
   - Log the event with structured format including mouse coordinates, element details
   - Publish to Redis pub/sub channels (dom_events, click_events, form_events)
   - Handle CORS for browser requests
   - Return appropriate status codes

3. Include session management:
   - Generate/track session IDs
   - Correlate events within user sessions
   - Handle anonymous vs identified users
   - Session timeout and cleanup

4. Add performance monitoring:
   - Track event ingestion rates
   - Monitor payload sizes
   - Log processing latencies
   - Handle high-volume click streams

Use async processing for high-volume DOM events. Include proper error handling and rate limiting.
```
```
Create Pydantic models for Shopify webhook events in apps/shopify_webhook_handler/models.py:

1. Create models for the following Shopify webhook events:
   - Cart creation/update events
   - Product view events
   - Checkout creation/update events
   - Customer events (creation, update)
   - Order events (creation, payment, fulfillment)

2. Each model should:
   - Include all relevant fields from Shopify webhook payloads
   - Have proper field validation
   - Include timestamp handling
   - Have a method to convert to a standardized event format for Redis

3. Create a base EventModel class that includes:
   - event_id (UUID)
   - event_type (enum)
   - timestamp
   - shop_domain
   - customer_id (optional)
   - session_id (optional)

4. Create an EventProcessor class that:
   - Takes raw webhook data
   - Validates against appropriate model
   - Converts to standardized format
   - Adds metadata (processing timestamp, event source)

Include comprehensive field validation and error handling.
```

#### Prompt 5: Shopify Webhook Models and Handler
```
Create Pydantic models and webhook handler for traditional Shopify events in apps/shopify_webhook_handler/:

1. Create models.py with Pydantic models for Shopify webhook events:
   - Cart creation/update events
   - Checkout creation/update events  
   - Customer events (creation, update)
   - Order events (creation, payment, fulfillment)

2. Create main.py with FastAPI application for webhooks:
   - Validate webhook authenticity using HMAC
   - Endpoints for different webhook types
   - Parse using appropriate Pydantic models
   - Publish to Redis channels (cart_events, checkout_events, order_events)
   - Handle errors gracefully with proper HTTP status codes

3. Include webhook verification and security:
   - HMAC signature validation
   - Request timestamp verification
   - Payload size limits
   - Rate limiting protection

Use the shared Redis client and logging configuration. Focus on reliability and security.
```
```
Create the main webhook handler service in apps/shopify_webhook_handler/main.py:

1. Create a FastAPI application that:
   - Accepts POST requests for Shopify webhooks
   - Validates webhook authenticity using HMAC
   - Has endpoints for different webhook types:
     * /webhooks/carts/create
     * /webhooks/carts/update
     * /webhooks/checkouts/create
     * /webhooks/checkouts/update
     * /webhooks/orders/create
     * /webhooks/orders/paid
     * /webhooks/customers/create

2. Each endpoint should:
   - Validate the incoming webhook payload
   - Parse using appropriate Pydantic model
   - Log the received event with structured logging
   - Publish event to Redis pub/sub channel
   - Return appropriate HTTP status codes
   - Handle errors gracefully

3. Include middleware for:
   - Request logging
   - CORS handling
   - Request validation
   - Error handling

4. Add a health check endpoint that:
   - Checks Redis connectivity
   - Returns service status
   - Includes uptime and basic metrics

Use the shared Redis client and logging configuration. Include comprehensive error handling and validation.
```

### Phase 1.3: Event Processing (Day 5-6)

#### Prompt 6: Enhanced Event Processor for Multi-Stream Data
```
Create an enhanced event processor service in apps/event_processor/main.py that handles both webhook and Web Pixels events:

1. Subscribe to multiple Redis pub/sub channels:
   - webhook_events: Traditional Shopify webhooks (cart, checkout, order)
   - dom_events: Web Pixels DOM interactions (clicks, inputs, forms)
   - session_events: Correlated user session data

2. For each event type, implement specialized processing:
   - **DOM Events**: Log click patterns, form interactions, mouse behavior
   - **Webhook Events**: Log business events (cart updates, purchases)
   - **Session Correlation**: Link DOM interactions to business outcomes

3. Event processing logic:
   - Track user behavior patterns and session flows
   - Identify potential cart abandonment signals from DOM events
   - Correlate click patterns with conversion events
   - Log structured insights combining both data streams

4. Session management:
   - Reconstruct user journeys from DOM + webhook events
   - Track session duration and engagement metrics
   - Identify high-intent vs low-intent behavior patterns
   - Handle session timeouts and cleanup

5. Advanced logging with behavioral insights:
   - Mouse movement patterns indicating hesitation
   - Click density and interaction frequency
   - Form abandonment patterns
   - Page engagement duration and scroll behavior
   - Correlation between DOM behavior and purchase completion

Include async processing, proper error handling, and behavioral pattern recognition.
```
```
Create an event processor service in apps/event_processor/main.py that:

1. Subscribes to Redis pub/sub channels for different event types:
   - cart_events
   - checkout_events
   - customer_events
   - order_events

2. For each received event:
   - Deserialize the event data
   - Log the event with structured format including:
     * Event type and ID
     * Customer information (if available)
     * Cart/checkout details
     * Timestamp
     * Processing metadata
   - Validate event data integrity
   - Store basic metrics (event counts by type)

3. Include event processing logic that:
   - Handles different event types appropriately
   - Tracks user sessions and behavior patterns
   - Identifies potential cart abandonment scenarios
   - Logs actionable insights

4. Implement graceful shutdown handling:
   - Clean Redis connection closure
   - Proper signal handling
   - Flush remaining events

5. Add monitoring capabilities:
   - Event processing rates
   - Error rates and types
   - Queue depth monitoring
   - Performance metrics logging

Use async/await patterns for non-blocking event processing. Include comprehensive error handling and recovery mechanisms.
```

#### Prompt 7: Web Pixels JavaScript Implementation
```
Create the client-side Web Pixels implementation in web_pixels/pixel.js:

1. Create a Shopify Web Pixels extension that:
   - Subscribes to all relevant DOM events (clicked, input_changed, input_focused, input_blurred, form_submitted)
   - Captures detailed event data including mouse coordinates and element properties
   - Implements session tracking and user identification
   - Sends events to your Python backend endpoints

2. Event capture implementation:
   - Track click coordinates, element details (id, class, tagName, href, value)
   - Capture form interactions and input changes
   - Implement mouse movement tracking with throttling
   - Track page engagement metrics (time on page, scroll depth)

3. Session and user correlation:
   - Generate and maintain session IDs
   - Correlate with Shopify customer data when available
   - Handle anonymous users vs identified customers
   - Implement client-side caching for offline/retry scenarios

4. Performance optimization:
   - Implement event throttling for high-frequency events (mouse moves)
   - Batch events for efficient network usage
   - Handle network failures with retry logic
   - Minimize performance impact on the store

5. Privacy and compliance:
   - Respect Shopify's privacy settings and consent management
   - Implement data minimization practices
   - Handle opt-out scenarios gracefully

The pixel should send HTTP POST requests to your web_pixels_handler endpoints. Include proper error handling and fallback mechanisms.
```

### Phase 1.4: Integration and Testing (Day 7-9)

#### Prompt 8: Docker Integration and Multi-Service Orchestration
```
Create the Docker integration for the multi-service architecture:

1. Update docker-compose.yml to run three services:
   - shopify-webhooks: Traditional webhook handler
   - web-pixels-handler: DOM event handler from browser
   - event-processor: Combined stream processor
   - redis: Redis pub/sub and caching

2. Create main entry point script (main.py) that supports:
   - python main.py webhook-handler
   - python main.py web-pixels-handler  
   - python main.py event-processor
   - python main.py all

3. Include proper service networking:
   - Internal communication between services
   - External endpoints for Shopify webhooks and Web Pixels
   - Redis connectivity across all services
   - Health checks for each service

4. Environment configuration:
   - Separate configs for each service
   - Shared Redis and logging configuration  
   - Development vs production settings
   - Service discovery and port management

Include proper container orchestration, graceful shutdown, and service monitoring.
```

#### Prompt 9: Comprehensive Testing Framework
```
Create comprehensive tests for both webhook and Web Pixels integration:

1. Create test_webhook_handler.py with:
   - Unit tests for traditional Shopify webhook validation
   - HMAC signature verification tests
   - Mock webhook payload tests for cart, checkout, order events
   - Redis publishing verification

2. Create test_web_pixels_handler.py with:
   - Unit tests for Web Pixels event validation
   - Tests for click event processing with mouse coordinates
   - Form interaction event tests
   - Session correlation and tracking tests
   - CORS and browser request handling tests

3. Create enhanced test_event_processor.py with:
   - Multi-stream event processing tests
   - Session correlation tests between DOM and webhook events
   - Behavioral pattern recognition tests
   - Event deduplication and ordering tests

4. Integration tests:
   - End-to-end flow from Web Pixels → Redis → Event Processing
   - Combined webhook + DOM event correlation testing
   - Session reconstruction and user journey tests
   - Performance tests for high-volume DOM events

5. Test fixtures and utilities:
   - Mock Shopify webhook payloads
   - Simulated Web Pixels event sequences
   - Session correlation test scenarios
   - Load testing utilities for DOM event streams

Include proper test isolation, async testing patterns, and comprehensive coverage for both data streams.
```
```
Create comprehensive tests for the Shopify cart recovery application:

1. Create test_webhook_handler.py with:
   - Unit tests for webhook validation
   - Tests for HMAC signature verification
   - Mock Shopify webhook payload tests
   - Redis publishing verification tests
   - Error handling tests
   - Integration tests with test Redis instance

2. Create test_event_processor.py with:
   - Unit tests for event processing logic
   - Redis subscription and message handling tests
   - Event deserialization tests
   - Logging verification tests
   - Error recovery tests

3. Include test fixtures for:
   - Sample Shopify webhook payloads
   - Test Redis configuration
   - Mock customer and cart data
   - Test event scenarios

4. Create test configuration:
   - pytest.ini configuration
   - Test environment variables
   - Test docker-compose configuration
   - CI/CD ready test commands

5. Add integration tests that:
   - Test end-to-end webhook to event processor flow
   - Verify Redis pub/sub communication
   - Test Docker container integration
   - Validate logging output format

Include proper test isolation, cleanup, and comprehensive coverage.
```

### Phase 1.5: Documentation and Deployment (Day 10-12)

#### Prompt 10: Enhanced Documentation and Web Pixels Integration Guide
```
Create comprehensive documentation for the dual-stream architecture:

1. Enhanced README.md covering:
   - Architecture overview: Webhook + Web Pixels integration
   - Quick start guide for both data streams
   - Web Pixels installation in Shopify stores
   - Environment setup for multi-service architecture
   - API endpoint documentation for both webhook and DOM events

2. Web Pixels integration guide:
   - Step-by-step Shopify Web Pixels setup
   - Custom pixel installation instructions
   - Event schema documentation for DOM events
   - Session correlation and tracking explanation
   - Privacy and compliance considerations

3. Development and debugging tools:
   - Enhanced monitoring scripts for both data streams
   - Web Pixels event debugging utilities
   - Session correlation analysis tools
   - Performance monitoring for high-volume DOM events
   - Redis channel monitoring for multiple event types

4. Deployment documentation:
   - Production deployment for multi-service architecture
   - Environment variables for webhook and Web Pixels handlers
   - Scaling considerations for DOM event ingestion
   - Security setup for both webhook HMAC and CORS
   - Monitoring and alerting setup

5. Sample configurations and examples:
   - Web Pixels JavaScript integration examples
   - Event correlation and session analysis examples
   - Webhook + DOM event combined processing examples
   - Performance optimization configurations

Ensure documentation covers both technical implementation and business value of combined webhook + DOM event tracking.
```

## Validation Criteria for Each Phase

### Phase 1.1 Success Criteria:
- [ ] Docker compose starts all services successfully (webhooks + web pixels + event processor)
- [ ] Redis connection established and verified for multiple channels
- [ ] Configuration loads for multi-service architecture
- [ ] Structured logging works across webhook and DOM event streams

### Phase 1.2 Success Criteria:
- [ ] Web Pixels JavaScript loads and captures DOM events correctly
- [ ] Web Pixels handler accepts and validates browser-sent events
- [ ] DOM events (clicks, inputs, forms) are published to Redis channels
- [ ] CORS handling works for browser requests
- [ ] Session tracking and correlation functions properly

### Phase 1.3 Success Criteria:
- [ ] Shopify webhook endpoints accept and validate payloads
- [ ] HMAC signature verification works correctly
- [ ] Webhook events are successfully published to Redis channels
- [ ] Proper error handling for invalid webhook requests

### Phase 1.4 Success Criteria:
- [ ] Event processor subscribes to both webhook and DOM event channels
- [ ] Events from both streams are received, processed, and logged correctly
- [ ] Session correlation between DOM and webhook events works
- [ ] Behavioral pattern recognition and logging functions properly

### Phase 1.5 Success Criteria:
- [ ] All three services run independently and together
- [ ] Docker containers communicate properly across services
- [ ] Integration tests validate end-to-end multi-stream flow
- [ ] Performance tests handle high-volume DOM events

### Phase 1.6 Success Criteria:
- [ ] Complete documentation enables Web Pixels + webhook integration
- [ ] Monitoring utilities provide insights for both data streams
- [ ] Deployment guide covers multi-service architecture
- [ ] Web Pixels installation guide is accurate and complete

## Usage Instructions

For each prompt above:
1. Copy the prompt into Claude Code
2. Review and refine the generated code
3. Test the implementation thoroughly
4. Move to the next prompt only after validating success criteria
5. Iterate on any issues before proceeding

This systematic approach ensures a solid foundation for your MVP while maintaining code quality and proper architecture from the start.
