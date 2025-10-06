"""
Centralized logging configuration
"""

import logging
import sys
from typing import Optional


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    
    # Get log level from parameter or environment
    import os
    log_level = level or os.getenv('LOG_LEVEL', 'INFO')
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, log_level.upper()))
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger


class StructuredLogger:
    """
    Structured logging for better observability.
    Logs in JSON format for easy parsing.
    """
    
    def __init__(self, name: str):
        self.logger = get_logger(name)
    
    def log_event(self, event_type: str, **kwargs):
        """Log structured event"""
        import json
        log_data = {
            'event_type': event_type,
            'timestamp': self._get_timestamp(),
            **kwargs
        }
        self.logger.info(json.dumps(log_data))
    
    def log_error(self, error_type: str, error_message: str, **kwargs):
        """Log structured error"""
        import json
        log_data = {
            'error_type': error_type,
            'error_message': error_message,
            'timestamp': self._get_timestamp(),
            **kwargs
        }
        self.logger.error(json.dumps(log_data))
    
    @staticmethod
    def _get_timestamp():
        from datetime import datetime
        return datetime.utcnow().isoformat()