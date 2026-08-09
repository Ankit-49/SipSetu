"""Structured logging configuration for SipSetu."""

import logging
import os
import sys
from datetime import datetime
from typing import Any

from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""
    
    def add_fields(self, log_record: dict[str, Any], record: logging.LogRecord, message_dict: dict[str, Any]):
        super().add_fields(log_record, record, message_dict)
        
        # Add standard fields
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        
        # Add request context if available
        try:
            from flask import g, has_request_context, request
            if has_request_context():
                log_record['request_id'] = getattr(g, 'request_id', getattr(request, 'request_id', None))
                log_record['method'] = request.method
                log_record['path'] = request.path
                log_record['remote_addr'] = request.remote_addr
                log_record['user_agent'] = request.headers.get('User-Agent', '')
                
                # Add user context if authenticated
                if hasattr(g, 'current_user_id'):
                    log_record['user_id'] = g.current_user_id
                if hasattr(g, 'current_user_role'):
                    log_record['user_role'] = g.current_user_role
        except RuntimeError:
            # Outside request context
            pass
        
        # Add exception info if present
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)


class TextFormatter(logging.Formatter):
    """Human-readable text formatter for development."""
    
    def format(self, record: logging.LogRecord) -> str:
        # Add request context if available
        try:
            from flask import g, has_request_context, request
            if has_request_context():
                request_id = getattr(g, 'request_id', getattr(request, 'request_id', 'no-request-id'))
                user_info = ""
                if hasattr(g, 'current_user_id'):
                    user_info = f" user={g.current_user_id}"
                return f"{self.formatTime(record)} [{record.levelname}] {record.name}{user_info} req={request_id} {record.getMessage()}"
        except RuntimeError:
            pass
        
        return super().format(record)


def setup_logging(app=None):
    """Configure application logging."""
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    log_format = os.environ.get('LOG_FORMAT', 'json').lower()
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    
    if log_format == 'json':
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(logger)s %(message)s',
            rename_fields={'levelname': 'level'}
        )
    else:
        formatter = TextFormatter(
            '%(asctime)s [%(levelname)s] %(name)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    
    # Reduce noise from third-party loggers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('redis').setLevel(logging.WARNING)
    
    # Flask app logger
    if app:
        app.logger.handlers.clear()
        app.logger.addHandler(handler)
        app.logger.setLevel(log_level)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


# Request logging middleware
def log_request_middleware(app):
    """Add request/response logging to Flask app."""
    
    @app.before_request
    def log_request():
        import time
        import uuid

        from flask import g, request
        
        # Generate request ID
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        g.request_id = request_id
        g.request_start_time = time.time()
        
        # Log request
        logger = logging.getLogger('request')
        logger.info(
            "Request started",
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.path,
                'query_string': request.query_string.decode() if request.query_string else '',
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'content_type': request.content_type,
                'content_length': request.content_length,
            }
        )
    
    @app.after_request
    def log_response(response):
        import time

        from flask import g, request
        
        # Calculate duration
        start_time = getattr(g, 'request_start_time', time.time())
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log response
        logger = logging.getLogger('request')
        logger.info(
            "Request completed",
            extra={
                'request_id': getattr(g, 'request_id', 'unknown'),
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'duration_ms': duration_ms,
                'response_size': response.content_length or 0,
            }
        )
        
        return response


# Structured logging helpers
def log_business_event(event_type: str, user_id: str = None, **kwargs):
    """Log a business event with structured data."""
    logger = logging.getLogger('business')
    logger.info(
        event_type,
        extra={
            'event_type': event_type,
            'user_id': user_id,
            **kwargs
        }
    )


def log_error(error: Exception, context: dict = None):
    """Log an error with structured context."""
    logger = logging.getLogger('error')
    logger.error(
        str(error),
        exc_info=True,
        extra={
            'error_type': type(error).__name__,
            'context': context or {}
        }
    )


def log_security_event(event_type: str, user_id: str = None, ip: str = None, **kwargs):
    """Log a security-related event."""
    logger = logging.getLogger('security')
    logger.warning(
        event_type,
        extra={
            'event_type': event_type,
            'security_event': True,
            'user_id': user_id,
            'ip': ip,
            **kwargs
        }
    )