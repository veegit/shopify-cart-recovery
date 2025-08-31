#!/usr/bin/env python3

import asyncio
import sys
import signal
import os
from typing import Optional

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from apps.shared.config import get_settings
from apps.shared.logging_config import get_logger

logger = get_logger("main")


class ServiceManager:
    def __init__(self):
        self.settings = get_settings()
        self.running_services = []
    
    async def start_webhook_handler(self):
        logger.info("Starting Shopify Webhook Handler")
        import uvicorn
        from apps.shopify_webhook_handler.main import app
        
        config = uvicorn.Config(
            app,
            host=self.settings.app.host,
            port=self.settings.app.port,
            log_config=None  # Use our custom logging
        )
        server = uvicorn.Server(config)
        await server.serve()
    
    async def start_web_pixels_handler(self):
        logger.info("Starting Web Pixels Handler")
        import uvicorn
        from apps.web_pixels_handler.main import app
        
        config = uvicorn.Config(
            app,
            host=self.settings.app.host,
            port=self.settings.app.port,
            log_config=None  # Use our custom logging
        )
        server = uvicorn.Server(config)
        await server.serve()
    
    async def start_event_processor(self):
        logger.info("Starting Event Processor")
        from apps.event_processor.main import main as processor_main
        await processor_main()
    
    async def start_all_services(self):
        logger.info("Starting all services")
        
        # Start event processor in background
        processor_task = asyncio.create_task(self.start_event_processor())
        
        # Start webhook handler on port 8001
        webhook_settings = self.settings
        webhook_settings.app.port = 8001
        
        webhook_task = asyncio.create_task(self.start_webhook_handler())
        
        # Start web pixels handler on port 8002  
        pixels_settings = self.settings
        pixels_settings.app.port = 8002
        
        pixels_task = asyncio.create_task(self.start_web_pixels_handler())
        
        self.running_services = [processor_task, webhook_task, pixels_task]
        
        try:
            await asyncio.gather(*self.running_services)
        except asyncio.CancelledError:
            logger.info("All services cancelled")
        except Exception as e:
            logger.error(f"Service error: {e}")
    
    def signal_handler(self, signum, frame):
        logger.info(f"Received signal {signum}, shutting down services")
        for task in self.running_services:
            if not task.done():
                task.cancel()
    
    async def health_check_all(self):
        from apps.shared.redis_client import get_redis_client
        
        try:
            redis_client = await get_redis_client()
            redis_healthy = await redis_client.health_check()
            
            health_status = {
                "redis": redis_healthy,
                "timestamp": str(asyncio.get_event_loop().time())
            }
            
            logger.info("Health check completed", health_status)
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"redis": False, "error": str(e)}


def print_usage():
    print("""
Usage: python main.py [SERVICE]

Services:
  webhook-handler     Start Shopify webhook handler
  web-pixels-handler  Start Web Pixels DOM event handler  
  event-processor     Start combined event processor
  all                 Start all services
  health              Run health check for all services

Examples:
  python main.py webhook-handler
  python main.py web-pixels-handler
  python main.py event-processor
  python main.py all
  python main.py health
""")


async def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    service = sys.argv[1].lower()
    manager = ServiceManager()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, manager.signal_handler)
    signal.signal(signal.SIGTERM, manager.signal_handler)
    
    try:
        if service == "webhook-handler":
            await manager.start_webhook_handler()
        elif service == "web-pixels-handler":
            await manager.start_web_pixels_handler()
        elif service == "event-processor":
            await manager.start_event_processor()
        elif service == "all":
            await manager.start_all_services()
        elif service == "health":
            health = await manager.health_check_all()
            print(f"Health Status: {health}")
            sys.exit(0 if health.get("redis") else 1)
        else:
            print(f"Unknown service: {service}")
            print_usage()
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Service startup failed: {e}")
        sys.exit(1)
    finally:
        from apps.shared.redis_client import close_redis_client
        await close_redis_client()
        logger.info("Service shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())