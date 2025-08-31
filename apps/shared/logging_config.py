import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any
from .config import get_settings


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "component": getattr(record, 'component', 'unknown'),
            "message": record.getMessage(),
        }
        
        if hasattr(record, 'extra_data'):
            log_entry.update(record.extra_data)
        
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)


class ComponentLogger:
    def __init__(self, component_name: str):
        self.component_name = component_name
        self.logger = logging.getLogger(component_name)
    
    def _log(self, level: int, message: str, extra_data: Dict[str, Any] = None):
        extra = {"component": self.component_name}
        if extra_data:
            extra["extra_data"] = extra_data
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, extra_data: Dict[str, Any] = None):
        self._log(logging.DEBUG, message, extra_data)
    
    def info(self, message: str, extra_data: Dict[str, Any] = None):
        self._log(logging.INFO, message, extra_data)
    
    def warning(self, message: str, extra_data: Dict[str, Any] = None):
        self._log(logging.WARNING, message, extra_data)
    
    def error(self, message: str, extra_data: Dict[str, Any] = None):
        self._log(logging.ERROR, message, extra_data)
    
    def critical(self, message: str, extra_data: Dict[str, Any] = None):
        self._log(logging.CRITICAL, message, extra_data)


def setup_logging():
    settings = get_settings()
    
    log_level = getattr(logging, settings.logging.level.upper(), logging.INFO)
    
    if settings.app.env == "production":
        log_level = max(log_level, logging.WARNING)
    
    logging.basicConfig(
        level=log_level,
        handlers=[logging.StreamHandler(sys.stdout)],
        format="%(message)s"
    )
    
    if settings.logging.format.lower() == "json":
        formatter = JSONFormatter()
        for handler in logging.root.handlers:
            handler.setFormatter(formatter)


def get_logger(component_name: str) -> ComponentLogger:
    return ComponentLogger(component_name)


setup_logging()