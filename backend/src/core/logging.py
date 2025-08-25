"""
Structured logging configuration
"""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

import structlog
from pythonjsonlogger import jsonlogger

from .config import settings


class JSONFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        super(JSONFormatter, self).add_fields(log_record, record, message_dict)
        
        # Add timestamp
        if not log_record.get('timestamp'):
            log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Add service info
        log_record['service'] = 'vils-backend'
        log_record['version'] = '1.0.0'
        log_record['environment'] = settings.environment
        
        # Add level name
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname


def setup_logging():
    """Configure structured logging"""
    
    # Configure structlog
    structlog.configure(
        processors=[
            # Filter out sensitive information
            structlog.stdlib.filter_by_level,
            # Add log level
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            # Add timestamp
            structlog.processors.TimeStamper(fmt="iso"),
            # Stack info for exceptions
            structlog.processors.StackInfoRenderer(),
            # Format exceptions
            structlog.processors.format_exc_info,
            # Convert to dictionary
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = JSONFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for all logs
    file_handler = logging.FileHandler(log_dir / "app.log")
    file_formatter = JSONFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.FileHandler(log_dir / "error.log")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)
    
    # Access log handler (for API requests)
    access_handler = logging.FileHandler(log_dir / "access.log")
    access_formatter = JSONFormatter(
        '%(timestamp)s %(method)s %(path)s %(status_code)s %(response_time)s'
    )
    access_handler.setFormatter(access_formatter)
    
    # Create access logger
    access_logger = logging.getLogger("access")
    access_logger.addHandler(access_handler)
    access_logger.propagate = False
    
    # Silence noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    return structlog.get_logger()


def get_logger(name: str = None) -> structlog.stdlib.BoundLogger:
    """Get structured logger instance"""
    return structlog.get_logger(name)


class RequestContextMiddleware:
    """Middleware to add request context to logs"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Extract request info
            request_id = scope.get("headers", {}).get("x-request-id", "unknown")
            method = scope.get("method", "unknown")
            path = scope.get("path", "unknown")
            
            # Add to structlog context
            structlog.contextvars.clear_contextvars()
            structlog.contextvars.bind_contextvars(
                request_id=request_id,
                method=method,
                path=path
            )
        
        await self.app(scope, receive, send)


# Logging utilities
def log_api_request(method: str, path: str, status_code: int, response_time: float, user_id: Optional[str] = None):
    """Log API request"""
    access_logger = logging.getLogger("access")
    access_logger.info(
        "API Request",
        extra={
            "method": method,
            "path": path,
            "status_code": status_code,
            "response_time": response_time,
            "user_id": user_id
        }
    )


def log_task_event(task_id: str, event: str, details: Optional[Dict[str, Any]] = None):
    """Log task-related events"""
    logger = get_logger("tasks")
    logger.info(
        f"Task {event}",
        task_id=task_id,
        event=event,
        details=details or {}
    )


def log_security_event(event: str, user_id: Optional[str] = None, ip_address: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
    """Log security-related events"""
    logger = get_logger("security")
    logger.warning(
        f"Security event: {event}",
        event=event,
        user_id=user_id,
        ip_address=ip_address,
        details=details or {}
    )


def log_error(error: Exception, context: Optional[Dict[str, Any]] = None):
    """Log errors with context"""
    logger = get_logger("errors")
    logger.error(
        "Application error",
        error=str(error),
        error_type=type(error).__name__,
        context=context or {},
        exc_info=True
    )


# Initialize logging
logger = setup_logging()