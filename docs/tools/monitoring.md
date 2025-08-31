# Development & Debugging Tools

Comprehensive monitoring and debugging utilities for the dual-stream Shopify Cart Recovery system.

## 🔍 Enhanced Monitoring Scripts

### Multi-Stream Event Monitor

Monitor events across all Redis channels in real-time:

```bash
#!/bin/bash
# scripts/monitor_events.sh

echo "🔍 Starting Multi-Stream Event Monitor..."
echo "Monitoring channels: cart_events, checkout_events, order_events, click_events, dom_events, form_events"
echo "Press Ctrl+C to stop"
echo ""

redis-cli --csv PSUBSCRIBE "*_events" | while IFS=',' read -r type channel message; do
    if [ "$type" = "pmessage" ]; then
        timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        channel_clean=$(echo $channel | tr -d '"')
        
        # Color coding by channel type
        case $channel_clean in
            *cart*) color="\033[32m" ;;      # Green for cart events
            *checkout*) color="\033[33m" ;;  # Yellow for checkout events
            *order*) color="\033[31m" ;;     # Red for order events  
            *click*) color="\033[34m" ;;     # Blue for click events
            *dom*) color="\033[35m" ;;       # Magenta for DOM events
            *form*) color="\033[36m" ;;      # Cyan for form events
            *) color="\033[0m" ;;            # Default
        esac
        
        echo -e "${color}[$timestamp] $channel_clean${color}\033[0m"
        echo "$message" | jq '.' 2>/dev/null || echo "$message"
        echo "----------------------------------------"
    fi
done
```

### Session Correlation Analyzer

Track and analyze user session flows:

```bash
#!/bin/bash
# scripts/analyze_sessions.sh

SESSION_ID=${1:-""}

if [ -z "$SESSION_ID" ]; then
    echo "Usage: $0 <session_id>"
    echo "Available sessions:"
    redis-cli --scan --pattern "*session*" | head -10
    exit 1
fi

echo "🔗 Analyzing Session: $SESSION_ID"
echo "=================================="

# Monitor session-specific events
redis-cli --csv PSUBSCRIBE "*_events" | while IFS=',' read -r type channel message; do
    if [ "$type" = "pmessage" ]; then
        if echo "$message" | grep -q "$SESSION_ID"; then
            timestamp=$(date '+%Y-%m-%d %H:%M:%S')
            channel_clean=$(echo $channel | tr -d '"')
            
            echo "[$timestamp] $channel_clean"
            echo "$message" | jq '.event_type, .data.element_tag, .data.clientX, .data.clientY' 2>/dev/null
            echo "---"
        fi
    fi
done
```

### Performance Dashboard Script

```python
#!/usr/bin/env python3
# scripts/performance_dashboard.py

import asyncio
import aioredis
import json
import time
from datetime import datetime, timedelta
import requests

class PerformanceDashboard:
    def __init__(self):
        self.redis = None
        self.metrics = {
            'events_per_second': 0,
            'total_events': 0,
            'active_sessions': 0,
            'channel_stats': {},
            'error_rate': 0
        }
    
    async def connect_redis(self):
        self.redis = await aioredis.from_url("redis://localhost:6379")
    
    async def collect_metrics(self):
        """Collect performance metrics from all services"""
        
        # Service health checks
        services = {
            'webhooks': 'http://localhost:8001/metrics',
            'pixels': 'http://localhost:8002/metrics'
        }
        
        for service, url in services.items():
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    self.metrics[f'{service}_healthy'] = True
                    self.metrics[f'{service}_metrics'] = data
                else:
                    self.metrics[f'{service}_healthy'] = False
            except:
                self.metrics[f'{service}_healthy'] = False
        
        # Redis channel statistics
        channels = ['cart_events', 'checkout_events', 'order_events', 
                   'click_events', 'dom_events', 'form_events']
        
        for channel in channels:
            try:
                # Get subscriber count
                info = await self.redis.pubsub_channels(channel)
                subscribers = await self.redis.pubsub_numsub(channel)
                self.metrics['channel_stats'][channel] = {
                    'exists': channel in info,
                    'subscribers': subscribers[0][1] if subscribers else 0
                }
            except Exception as e:
                self.metrics['channel_stats'][channel] = {'error': str(e)}
    
    def display_dashboard(self):
        """Display real-time performance dashboard"""
        import os
        os.system('clear')
        
        print("🚀 Shopify Cart Recovery - Performance Dashboard")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Service Health
        print("🏥 Service Health:")
        webhook_status = "🟢 Online" if self.metrics.get('webhooks_healthy') else "🔴 Offline"
        pixels_status = "🟢 Online" if self.metrics.get('pixels_healthy') else "🔴 Offline"
        print(f"  Webhook Handler: {webhook_status}")
        print(f"  Web Pixels Handler: {pixels_status}")
        print()
        
        # Performance Metrics
        if 'pixels_metrics' in self.metrics:
            pixels_data = self.metrics['pixels_metrics']
            if 'performance' in pixels_data:
                perf = pixels_data['performance']
                print("📊 Performance Metrics:")
                print(f"  Events/Second: {perf.get('events_per_second', 0):.1f}")
                print(f"  Total Events: {perf.get('total_events', 0):,}")
                print(f"  Avg Processing Time: {perf.get('avg_processing_time_ms', 0):.2f}ms")
                print()
        
        # Channel Statistics
        print("📡 Redis Channel Statistics:")
        for channel, stats in self.metrics.get('channel_stats', {}).items():
            if 'error' not in stats:
                status = "🟢" if stats.get('exists') else "⚪"
                subs = stats.get('subscribers', 0)
                print(f"  {status} {channel}: {subs} subscribers")
        print()
        
        # Session Information
        if 'pixels_metrics' in self.metrics:
            pixels_data = self.metrics['pixels_metrics']
            if 'sessions' in pixels_data:
                sessions = pixels_data['sessions']
                print("👥 Session Statistics:")
                print(f"  Active Sessions: {sessions.get('active_count', 0)}")
                print(f"  Total Events: {sessions.get('total_events', 0)}")
                print()

async def run_dashboard():
    dashboard = PerformanceDashboard()
    await dashboard.connect_redis()
    
    try:
        while True:
            await dashboard.collect_metrics()
            dashboard.display_dashboard()
            await asyncio.sleep(5)
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped")

if __name__ == "__main__":
    asyncio.run(run_dashboard())
```

## 🐛 Web Pixels Event Debugger

### Browser Console Debugger

```javascript
// scripts/debug_pixels.js
// Paste into browser console for Web Pixels debugging

class WebPixelsDebugger {
    constructor() {
        this.events = [];
        this.sessionId = null;
        this.customerId = null;
        this.startTime = Date.now();
        this.init();
    }
    
    init() {
        console.log('🔍 Web Pixels Debugger initialized');
        this.injectDebugger();
        this.monitorNetworkRequests();
        this.trackPixelEvents();
    }
    
    injectDebugger() {
        // Override fetch to intercept pixel requests
        const originalFetch = window.fetch;
        
        window.fetch = async (...args) => {
            const [url, options] = args;
            
            if (url.includes('/pixels/')) {
                console.log('🚀 Pixel Event Sent:', {
                    url,
                    method: options?.method,
                    headers: options?.headers,
                    body: options?.body ? JSON.parse(options.body) : null,
                    timestamp: new Date().toISOString()
                });
                
                this.events.push({
                    type: 'network_request',
                    url,
                    timestamp: Date.now(),
                    data: options?.body ? JSON.parse(options.body) : null
                });
            }
            
            return originalFetch(...args);
        };
    }
    
    monitorNetworkRequests() {
        // Monitor network responses
        const observer = new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) {
                if (entry.name.includes('/pixels/')) {
                    console.log('📡 Network Response:', {
                        url: entry.name,
                        duration: entry.duration,
                        transferSize: entry.transferSize,
                        responseStatus: entry.responseStatus
                    });
                }
            }
        });
        
        observer.observe({ type: 'navigation', buffered: true });
        observer.observe({ type: 'resource', buffered: true });
    }
    
    trackPixelEvents() {
        // Monitor DOM events that should trigger pixels
        const events = ['click', 'input', 'focus', 'blur', 'submit'];
        
        events.forEach(eventType => {
            document.addEventListener(eventType, (e) => {
                console.log(`🎯 DOM Event: ${eventType}`, {
                    target: e.target.tagName,
                    id: e.target.id,
                    class: e.target.className,
                    coordinates: eventType === 'click' ? 
                        { x: e.clientX, y: e.clientY } : null,
                    timestamp: Date.now()
                });
            }, true);
        });
    }
    
    getSessionInfo() {
        return {
            sessionId: sessionStorage.getItem('web_pixels_session_id'),
            customerId: window.Shopify?.customerID || window.__st?.cid,
            trackerExists: !!window.WebPixelsTracker,
            eventsRecorded: this.events.length,
            sessionDuration: Date.now() - this.startTime
        };
    }
    
    testPixelEndpoint(eventType = 'clicked') {
        const testData = {
            clientX: 100,
            clientY: 200,
            element_tag: 'button',
            element_id: 'test-button',
            url: window.location.href
        };
        
        if (window.WebPixelsTracker) {
            window.WebPixelsTracker.queueEvent(eventType, testData);
            console.log('✅ Test event queued:', eventType, testData);
        } else {
            console.error('❌ WebPixelsTracker not found');
        }
    }
    
    showDebugSummary() {
        const info = this.getSessionInfo();
        console.table(info);
        console.log('📊 Recorded Events:', this.events);
    }
}

// Initialize debugger
const pixelDebugger = new WebPixelsDebugger();

// Add to global scope for manual testing
window.pixelDebugger = pixelDebugger;

console.log(`
🔧 Web Pixels Debugger Commands:
  pixelDebugger.getSessionInfo() - Get session information
  pixelDebugger.testPixelEndpoint() - Send test event
  pixelDebugger.showDebugSummary() - Show debug summary
`);
```

### Network Traffic Analyzer

```bash
#!/bin/bash
# scripts/analyze_traffic.sh

echo "📊 Analyzing Web Pixels Traffic..."

# Monitor HTTP requests to pixel endpoints
sudo tcpdump -i any -A -s 0 'host localhost and port 8002' | while read line; do
    if [[ $line == *"/pixels/"* ]]; then
        timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        echo "[$timestamp] Pixel Request: $line"
    fi
done
```

## 🔧 Session Correlation Analysis Tools

### Session Journey Reconstructor

```python
#!/usr/bin/env python3
# scripts/session_analyzer.py

import asyncio
import aioredis
import json
from collections import defaultdict
from datetime import datetime

class SessionAnalyzer:
    def __init__(self):
        self.sessions = defaultdict(list)
        self.redis = None
    
    async def connect(self):
        self.redis = await aioredis.from_url("redis://localhost:6379")
    
    async def analyze_session(self, session_id):
        """Analyze a specific session's journey"""
        print(f"🔍 Analyzing Session: {session_id}")
        print("=" * 50)
        
        # Collect all events for this session
        channels = ['cart_events', 'checkout_events', 'order_events', 
                   'click_events', 'dom_events', 'form_events']
        
        events = []
        
        # Subscribe to channels and collect historical data
        pubsub = self.redis.pubsub()
        await pubsub.psubscribe('*_events')
        
        print("📡 Collecting session events...")
        
        async for message in pubsub.listen():
            if message['type'] == 'pmessage':
                try:
                    data = json.loads(message['data'])
                    if data.get('session_id') == session_id:
                        events.append(data)
                        self.display_event(data)
                except json.JSONDecodeError:
                    pass
    
    def display_event(self, event):
        """Display event in readable format"""
        timestamp = event.get('timestamp', 'N/A')
        event_type = event.get('event_type', 'unknown')
        source = event.get('source', 'unknown')
        
        # Color coding
        color = {
            'web_pixels': '\033[94m',     # Blue
            'shopify_webhook': '\033[92m' # Green
        }.get(source, '\033[0m')
        
        print(f"{color}[{timestamp}] {event_type} ({source})\033[0m")
        
        # Show relevant data based on event type
        data = event.get('data', {})
        if 'clientX' in data and 'clientY' in data:
            print(f"  Click: ({data['clientX']}, {data['clientY']}) on {data.get('element_tag', 'unknown')}")
        elif 'total_price' in data:
            print(f"  Value: {data['total_price']} {data.get('currency', 'USD')}")
        elif 'form_id' in data:
            print(f"  Form: {data['form_id']}")
        
        print()
    
    def analyze_patterns(self, session_events):
        """Analyze behavioral patterns in session"""
        click_events = [e for e in session_events if e.get('event_type') == 'clicked']
        form_events = [e for e in session_events if 'form' in e.get('event_type', '')]
        webhook_events = [e for e in session_events if e.get('source') == 'shopify_webhook']
        
        print("📊 Session Analysis:")
        print(f"  Total Events: {len(session_events)}")
        print(f"  Click Events: {len(click_events)}")
        print(f"  Form Events: {len(form_events)}")
        print(f"  Business Events: {len(webhook_events)}")
        
        # Calculate click density
        if len(click_events) > 1:
            coordinates = [(e['data']['clientX'], e['data']['clientY']) 
                          for e in click_events if 'data' in e]
            avg_distance = self.calculate_click_dispersion(coordinates)
            print(f"  Click Pattern: {'Focused' if avg_distance < 100 else 'Scattered'}")
        
        # Conversion analysis
        has_cart = any('cart' in e.get('event_type', '') for e in webhook_events)
        has_order = any('order' in e.get('event_type', '') for e in webhook_events)
        
        if has_order:
            print("  Outcome: ✅ Conversion")
        elif has_cart:
            print("  Outcome: ⚠️ Cart Abandonment")
        else:
            print("  Outcome: 👀 Browsing Only")
    
    def calculate_click_dispersion(self, coordinates):
        """Calculate average distance between clicks"""
        if len(coordinates) < 2:
            return 0
        
        total_distance = 0
        count = 0
        
        for i in range(len(coordinates) - 1):
            x1, y1 = coordinates[i]
            x2, y2 = coordinates[i + 1]
            distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
            total_distance += distance
            count += 1
        
        return total_distance / count if count > 0 else 0

async def main():
    analyzer = SessionAnalyzer()
    await analyzer.connect()
    
    session_id = input("Enter session ID to analyze: ")
    await analyzer.analyze_session(session_id)

if __name__ == "__main__":
    asyncio.run(main())
```

## 📡 Redis Channel Monitor

### Advanced Channel Monitoring

```python
#!/usr/bin/env python3
# scripts/redis_monitor.py

import asyncio
import aioredis
import json
from datetime import datetime
from collections import defaultdict, deque

class RedisChannelMonitor:
    def __init__(self):
        self.redis = None
        self.stats = defaultdict(lambda: {
            'count': 0,
            'last_seen': None,
            'events_per_minute': deque(maxlen=60),
            'error_count': 0
        })
        self.start_time = datetime.now()
    
    async def connect(self):
        self.redis = await aioredis.from_url("redis://localhost:6379")
        print("✅ Connected to Redis")
    
    async def monitor_all_channels(self):
        """Monitor all event channels"""
        pubsub = self.redis.pubsub()
        await pubsub.psubscribe('*_events')
        
        print("🔍 Monitoring all event channels...")
        print("Press Ctrl+C to stop")
        print()
        
        async for message in pubsub.listen():
            if message['type'] == 'pmessage':
                await self.process_message(message)
    
    async def process_message(self, message):
        """Process and analyze incoming message"""
        channel = message['channel'].decode('utf-8')
        
        try:
            data = json.loads(message['data'])
            self.update_stats(channel, data)
            self.display_event(channel, data)
        except json.JSONDecodeError as e:
            self.stats[channel]['error_count'] += 1
            print(f"❌ JSON decode error in {channel}: {e}")
    
    def update_stats(self, channel, data):
        """Update channel statistics"""
        stats = self.stats[channel]
        stats['count'] += 1
        stats['last_seen'] = datetime.now()
        
        # Track events per minute
        current_minute = datetime.now().minute
        if not stats['events_per_minute'] or stats['events_per_minute'][-1][0] != current_minute:
            stats['events_per_minute'].append((current_minute, 1))
        else:
            stats['events_per_minute'][-1] = (current_minute, stats['events_per_minute'][-1][1] + 1)
    
    def display_event(self, channel, data):
        """Display event information"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        event_type = data.get('event_type', 'unknown')
        session_id = data.get('session_id', 'N/A')
        
        # Channel color coding
        colors = {
            'cart_events': '\033[92m',      # Green
            'checkout_events': '\033[93m',  # Yellow
            'order_events': '\033[91m',     # Red
            'click_events': '\033[94m',     # Blue
            'dom_events': '\033[95m',       # Magenta
            'form_events': '\033[96m'       # Cyan
        }
        color = colors.get(channel, '\033[0m')
        
        print(f"{color}[{timestamp}] {channel}: {event_type} (session: {session_id[:8]}...)\033[0m")
    
    def display_summary(self):
        """Display monitoring summary"""
        import os
        os.system('clear')
        
        runtime = datetime.now() - self.start_time
        
        print("📊 Redis Channel Monitor - Live Statistics")
        print("=" * 60)
        print(f"Runtime: {runtime}")
        print()
        
        print("📡 Channel Statistics:")
        for channel, stats in self.stats.items():
            events_per_min = sum(count for _, count in stats['events_per_minute'])
            last_seen = stats['last_seen'].strftime('%H:%M:%S') if stats['last_seen'] else 'Never'
            
            print(f"  {channel}:")
            print(f"    Events: {stats['count']:,}")
            print(f"    Rate: {events_per_min}/min")
            print(f"    Last: {last_seen}")
            print(f"    Errors: {stats['error_count']}")
            print()
        
        total_events = sum(stats['count'] for stats in self.stats.values())
        total_errors = sum(stats['error_count'] for stats in self.stats.values())
        
        print(f"Total Events: {total_events:,}")
        print(f"Total Errors: {total_errors}")
        print(f"Error Rate: {(total_errors/total_events*100) if total_events else 0:.2f}%")

async def monitor_with_summary():
    """Monitor with periodic summary updates"""
    monitor = RedisChannelMonitor()
    await monitor.connect()
    
    async def summary_task():
        while True:
            await asyncio.sleep(10)
            monitor.display_summary()
    
    # Run monitoring and summary concurrently
    try:
        await asyncio.gather(
            monitor.monitor_all_channels(),
            summary_task()
        )
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped")

if __name__ == "__main__":
    asyncio.run(monitor_with_summary())
```

## 🚨 Error Detection & Alerting

### Error Pattern Detector

```bash
#!/bin/bash
# scripts/error_detector.sh

LOG_FILE="/var/log/shopify-cart-recovery.log"
ALERT_THRESHOLD=10
ALERT_EMAIL="admin@yourcompany.com"

echo "🚨 Error Pattern Detector Started"

monitor_errors() {
    tail -f "$LOG_FILE" | while read line; do
        # Detect different error patterns
        if echo "$line" | grep -q "ERROR\|CRITICAL"; then
            echo "🔴 $(date): $line"
            
            # Count recent errors
            recent_errors=$(tail -100 "$LOG_FILE" | grep -c "ERROR\|CRITICAL")
            
            if [ "$recent_errors" -gt "$ALERT_THRESHOLD" ]; then
                send_alert "$line" "$recent_errors"
            fi
        fi
        
        # Detect specific patterns
        if echo "$line" | grep -q "Redis.*connection.*failed"; then
            echo "⚠️  Redis connection issue detected"
            send_redis_alert "$line"
        fi
        
        if echo "$line" | grep -q "HMAC.*verification.*failed"; then
            echo "🔒 Security: HMAC verification failed"
            send_security_alert "$line"
        fi
    done
}

send_alert() {
    local error_line="$1"
    local error_count="$2"
    
    echo "📧 Sending alert: $error_count errors detected"
    
    # Send email alert (configure your mail system)
    echo "High error rate detected: $error_count recent errors" | \
        mail -s "Shopify Cart Recovery: High Error Rate" "$ALERT_EMAIL"
}

send_redis_alert() {
    echo "📨 Redis connection alert sent"
    # Implement Redis-specific alerting
}

send_security_alert() {
    echo "🔐 Security alert sent"
    # Implement security-specific alerting
}

# Start monitoring
monitor_errors
```

## 📊 Performance Monitoring

### Real-time Performance Tracker

```python
#!/usr/bin/env python3
# scripts/performance_tracker.py

import asyncio
import aioredis
import aiohttp
import time
from datetime import datetime, timedelta

class PerformanceTracker:
    def __init__(self):
        self.metrics = {
            'webhook_latency': [],
            'pixels_latency': [],
            'redis_ops': [],
            'event_processing_rate': 0,
            'memory_usage': 0,
            'cpu_usage': 0
        }
        self.start_time = time.time()
    
    async def test_webhook_latency(self):
        """Test webhook endpoint response time"""
        url = "http://localhost:8001/health"
        
        async with aiohttp.ClientSession() as session:
            start = time.time()
            try:
                async with session.get(url) as response:
                    latency = (time.time() - start) * 1000
                    self.metrics['webhook_latency'].append(latency)
                    return latency, response.status == 200
            except Exception as e:
                return None, False
    
    async def test_pixels_latency(self):
        """Test Web Pixels endpoint response time"""
        url = "http://localhost:8002/health"
        
        async with aiohttp.ClientSession() as session:
            start = time.time()
            try:
                async with session.get(url) as response:
                    latency = (time.time() - start) * 1000
                    self.metrics['pixels_latency'].append(latency)
                    return latency, response.status == 200
            except Exception as e:
                return None, False
    
    async def test_redis_performance(self):
        """Test Redis operation performance"""
        redis = await aioredis.from_url("redis://localhost:6379")
        
        start = time.time()
        try:
            await redis.ping()
            latency = (time.time() - start) * 1000
            self.metrics['redis_ops'].append(latency)
            return latency, True
        except Exception as e:
            return None, False
        finally:
            await redis.close()
    
    async def collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            import psutil
            self.metrics['memory_usage'] = psutil.virtual_memory().percent
            self.metrics['cpu_usage'] = psutil.cpu_percent()
        except ImportError:
            # psutil not available
            pass
    
    def calculate_averages(self):
        """Calculate average metrics"""
        return {
            'avg_webhook_latency': sum(self.metrics['webhook_latency'][-10:]) / min(len(self.metrics['webhook_latency']), 10) if self.metrics['webhook_latency'] else 0,
            'avg_pixels_latency': sum(self.metrics['pixels_latency'][-10:]) / min(len(self.metrics['pixels_latency']), 10) if self.metrics['pixels_latency'] else 0,
            'avg_redis_latency': sum(self.metrics['redis_ops'][-10:]) / min(len(self.metrics['redis_ops']), 10) if self.metrics['redis_ops'] else 0,
        }
    
    def display_metrics(self):
        """Display current performance metrics"""
        import os
        os.system('clear')
        
        uptime = time.time() - self.start_time
        averages = self.calculate_averages()
        
        print("⚡ Performance Metrics Dashboard")
        print("=" * 40)
        print(f"Uptime: {uptime:.0f}s")
        print()
        
        print("🌐 API Latency (ms):")
        print(f"  Webhook Handler: {averages['avg_webhook_latency']:.1f}ms")
        print(f"  Pixels Handler:  {averages['avg_pixels_latency']:.1f}ms")
        print(f"  Redis Ops:       {averages['avg_redis_latency']:.1f}ms")
        print()
        
        if self.metrics['memory_usage']:
            print("💾 System Resources:")
            print(f"  Memory Usage: {self.metrics['memory_usage']:.1f}%")
            print(f"  CPU Usage:    {self.metrics['cpu_usage']:.1f}%")
            print()
        
        # Performance status
        webhook_ok = averages['avg_webhook_latency'] < 100
        pixels_ok = averages['avg_pixels_latency'] < 100
        redis_ok = averages['avg_redis_latency'] < 10
        
        status = "🟢 All systems optimal" if all([webhook_ok, pixels_ok, redis_ok]) else "⚠️ Performance issues detected"
        print(f"Status: {status}")

async def run_performance_monitor():
    tracker = PerformanceTracker()
    
    async def collect_metrics():
        while True:
            await tracker.test_webhook_latency()
            await tracker.test_pixels_latency() 
            await tracker.test_redis_performance()
            await tracker.collect_system_metrics()
            await asyncio.sleep(5)
    
    async def display_loop():
        while True:
            tracker.display_metrics()
            await asyncio.sleep(2)
    
    try:
        await asyncio.gather(collect_metrics(), display_loop())
    except KeyboardInterrupt:
        print("\n👋 Performance monitor stopped")

if __name__ == "__main__":
    asyncio.run(run_performance_monitor())
```

---

## 🎯 Usage Instructions

### Quick Start Monitoring

```bash
# Make all scripts executable
chmod +x scripts/*.sh scripts/*.py

# Start basic event monitoring
./scripts/monitor_events.sh

# Monitor specific session
./scripts/analyze_sessions.sh session_id_here

# Performance dashboard
python3 scripts/performance_dashboard.py

# Error detection
./scripts/error_detector.sh
```

### Advanced Debugging Workflow

1. **Start Performance Monitor**
   ```bash
   python3 scripts/performance_tracker.py
   ```

2. **Open Browser Console** and paste the Web Pixels debugger
3. **Monitor Redis Channels** in another terminal
   ```bash
   python3 scripts/redis_monitor.py
   ```

4. **Analyze User Sessions** when issues detected
   ```bash
   python3 scripts/session_analyzer.py
   ```

### Production Monitoring Setup

```bash
# Add to crontab for regular checks
0 */4 * * * /path/to/scripts/error_detector.sh
*/5 * * * * /path/to/scripts/performance_tracker.py --check-only

# Set up log rotation
echo "/var/log/shopify-cart-recovery.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}" > /etc/logrotate.d/shopify-cart-recovery
```

These tools provide comprehensive monitoring and debugging capabilities for both the webhook and Web Pixels data streams, enabling rapid identification and resolution of issues in production environments.