"""
Centralized logging configuration with structured JSON logging
"""

import logging
import sys
import os
import json
from typing import Optional, Any, Dict
from datetime import datetime
from pythonjsonlogger import jsonlogger


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
    log_level = level or os.getenv('LOG_LEVEL', 'INFO')

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Determine if we should use JSON logging
    use_json = os.getenv('LOG_FORMAT', 'text').lower() == 'json'

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, log_level.upper()))

    if use_json:
        # JSON formatter for CloudWatch and production
        formatter = jsonlogger.JsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s %(pathname)s %(lineno)d',
            rename_fields={
                'levelname': 'level',
                'asctime': 'timestamp',
                'name': 'logger',
                'pathname': 'file',
                'lineno': 'line'
            }
        )
    else:
        # Human-readable formatter for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


class StructuredLogger:
    """
    Structured logging for better observability.
    Logs in JSON format for easy parsing in CloudWatch.
    """

    def __init__(self, name: str):
        self.logger = get_logger(name)
        self.service_name = os.getenv('SERVICE_NAME', 'contractguard-ai')
        self.environment = os.getenv('APP_ENV', 'development')

    def _create_log_entry(self, **kwargs) -> Dict[str, Any]:
        """Create base log entry with common fields"""
        return {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'service': self.service_name,
            'environment': self.environment,
            **kwargs
        }

    def info(self, message: str, **kwargs):
        """Log info level message"""
        log_data = self._create_log_entry(
            level='INFO',
            message=message,
            **kwargs
        )
        self.logger.info(json.dumps(log_data))

    def warning(self, message: str, **kwargs):
        """Log warning level message"""
        log_data = self._create_log_entry(
            level='WARNING',
            message=message,
            **kwargs
        )
        self.logger.warning(json.dumps(log_data))

    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log error level message"""
        log_data = self._create_log_entry(
            level='ERROR',
            message=message,
            **kwargs
        )

        if error:
            log_data.update({
                'error_type': type(error).__name__,
                'error_message': str(error),
                'stack_trace': self._get_stack_trace(error)
            })

        self.logger.error(json.dumps(log_data))

    def log_contract_event(
        self,
        event_type: str,
        contract_id: str,
        user_id: str,
        **kwargs
    ):
        """Log contract-related event"""
        log_data = self._create_log_entry(
            level='INFO',
            event_type=event_type,
            contract_id=contract_id,
            user_id=user_id,
            **kwargs
        )
        self.logger.info(json.dumps(log_data))

    def log_api_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[str] = None,
        **kwargs
    ):
        """Log API request"""
        log_data = self._create_log_entry(
            level='INFO',
            event_type='api_request',
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            user_id=user_id,
            **kwargs
        )
        self.logger.info(json.dumps(log_data))

    def log_bedrock_invocation(
        self,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        duration_ms: float,
        **kwargs
    ):
        """Log Bedrock API invocation for cost tracking"""
        log_data = self._create_log_entry(
            level='INFO',
            event_type='bedrock_invocation',
            model_id=model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_ms=duration_ms,
            **kwargs
        )
        self.logger.info(json.dumps(log_data))

    def log_tool_execution(
        self,
        tool_name: str,
        contract_id: str,
        duration_ms: float,
        success: bool,
        **kwargs
    ):
        """Log Lambda tool execution"""
        log_data = self._create_log_entry(
            level='INFO' if success else 'ERROR',
            event_type='tool_execution',
            tool_name=tool_name,
            contract_id=contract_id,
            duration_ms=duration_ms,
            success=success,
            **kwargs
        )
        self.logger.info(json.dumps(log_data))

    @staticmethod
    def _get_stack_trace(error: Exception) -> str:
        """Get formatted stack trace"""
        import traceback
        return ''.join(traceback.format_exception(
            type(error), error, error.__traceback__
        ))


# Singleton instances for common loggers
_loggers: Dict[str, StructuredLogger] = {}


def get_structured_logger(name: str) -> StructuredLogger:
    """
    Get or create a structured logger instance.

    Args:
        name: Logger name

    Returns:
        StructuredLogger instance
    """
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name)
    return _loggers[name]