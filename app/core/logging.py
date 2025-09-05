"""
Enhanced logging configuration
"""
import logging
import logging.config
import sys
from typing import Any, Dict, Optional
from pathlib import Path
import json
from datetime import datetime

from .constants import LogLevel, Environment
from .config import settings


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors"""
        color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


class ContextFilter(logging.Filter):
    """Add context information to log records"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add context information"""
        # Add request ID if available
        if hasattr(record, 'request_id'):
            record.request_id = getattr(record, 'request_id', 'N/A')
        
        # Add user ID if available
        if hasattr(record, 'user_id'):
            record.user_id = getattr(record, 'user_id', 'N/A')
        
        # Add service name
        record.service = getattr(record, 'service', 'fastapi-framework')
        
        return True


def setup_logging(
    level: LogLevel = LogLevel.INFO,
    environment: Environment = Environment.DEVELOPMENT,
    log_file: Optional[str] = None,
    json_format: bool = False
) -> None:
    """Setup application logging"""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Determine log level
    log_level = getattr(logging, level.value, logging.INFO)
    
    # Configure formatters
    if json_format or environment == Environment.PRODUCTION:
        formatter = JSONFormatter()
    else:
        formatter = ColoredFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Configure handlers
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(ContextFilter())
    handlers.append(console_handler)
    
    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(ContextFilter())
        handlers.append(file_handler)
    
    # Error file handler
    error_handler = logging.FileHandler(log_dir / "error.log")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    error_handler.addFilter(ContextFilter())
    handlers.append(error_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        force=True
    )
    
    # Configure specific loggers
    loggers_config = {
        'app': logging.INFO,
        'uvicorn': logging.INFO,
        'uvicorn.access': logging.WARNING,
        'sqlalchemy.engine': logging.WARNING,
        'sqlalchemy.pool': logging.WARNING,
        'alembic': logging.INFO,
        'arq': logging.INFO,
        'prometheus': logging.INFO,
    }
    
    for logger_name, logger_level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(logger_level)
    
    # Suppress noisy loggers
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)


def log_request(logger: logging.Logger, request_id: str, method: str, url: str, **kwargs) -> None:
    """Log HTTP request"""
    logger.info(
        f"Request {request_id}: {method} {url}",
        extra={
            'request_id': request_id,
            'method': method,
            'url': str(url),
            'extra_fields': kwargs
        }
    )


def log_response(logger: logging.Logger, request_id: str, status_code: int, duration: float, **kwargs) -> None:
    """Log HTTP response"""
    logger.info(
        f"Response {request_id}: {status_code} ({duration:.3f}s)",
        extra={
            'request_id': request_id,
            'status_code': status_code,
            'duration': duration,
            'extra_fields': kwargs
        }
    )


def log_error(logger: logging.Logger, request_id: str, error: Exception, **kwargs) -> None:
    """Log error"""
    logger.error(
        f"Error {request_id}: {str(error)}",
        extra={
            'request_id': request_id,
            'error_type': type(error).__name__,
            'extra_fields': kwargs
        },
        exc_info=True
    )


def log_task(logger: logging.Logger, task_name: str, task_id: str, status: str, **kwargs) -> None:
    """Log task execution"""
    logger.info(
        f"Task {task_name} {task_id}: {status}",
        extra={
            'task_name': task_name,
            'task_id': task_id,
            'status': status,
            'extra_fields': kwargs
        }
    )


def log_metric(logger: logging.Logger, metric_name: str, value: float, **kwargs) -> None:
    """Log metric"""
    logger.info(
        f"Metric {metric_name}: {value}",
        extra={
            'metric_name': metric_name,
            'value': value,
            'extra_fields': kwargs
        }
    )


class LoggerMixin:
    """Mixin class for adding logging capabilities"""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class"""
        return get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")


# Initialize logging
def init_logging() -> None:
    """Initialize application logging"""
    setup_logging(
        level=LogLevel(settings.LOG_LEVEL),
        environment=Environment(settings.ENVIRONMENT),
        log_file="logs/app.log",
        json_format=settings.ENVIRONMENT == Environment.PRODUCTION
    )