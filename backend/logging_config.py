"""
Logging configuration for MOTOSPECT backend
"""
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime
import json

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        log_obj = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if hasattr(record, 'user_id'):
            log_obj['user_id'] = record.user_id
        if hasattr(record, 'session_id'):
            log_obj['session_id'] = record.session_id
        if hasattr(record, 'vehicle_vin'):
            log_obj['vehicle_vin'] = record.vehicle_vin
            
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_obj)


def setup_logging(
    app_name: str = "motospect",
    debug_mode: bool = False,
    log_dir: str = "/app/logs",
    enable_json: bool = False
):
    """
    Setup comprehensive logging configuration
    
    Args:
        app_name: Application name for log files
        debug_mode: Enable debug level logging
        log_dir: Directory for log files
        enable_json: Use JSON format for logs
    """
    
    # Create log directory if it doesn't exist
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Determine log level
    log_level = logging.DEBUG if debug_mode else logging.INFO
    
    # Create formatters
    if enable_json:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Console handler with color coding
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    if not enable_json:
        # Add color coding for console output
        class ColoredFormatter(logging.Formatter):
            COLORS = {
                'DEBUG': '\033[36m',    # Cyan
                'INFO': '\033[32m',     # Green
                'WARNING': '\033[33m',  # Yellow
                'ERROR': '\033[31m',    # Red
                'CRITICAL': '\033[35m', # Magenta
            }
            RESET = '\033[0m'
            
            def format(self, record):
                log_color = self.COLORS.get(record.levelname, self.RESET)
                record.levelname = f"{log_color}{record.levelname}{self.RESET}"
                return super().format(record)
        
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
    else:
        console_handler.setFormatter(formatter)
    
    # File handlers
    # Main application log
    app_handler = logging.handlers.RotatingFileHandler(
        f"{log_dir}/{app_name}.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    app_handler.setLevel(log_level)
    app_handler.setFormatter(formatter)
    
    # Error log
    error_handler = logging.handlers.RotatingFileHandler(
        f"{log_dir}/{app_name}_error.log",
        maxBytes=10*1024*1024,
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    
    # Debug log (only in debug mode)
    debug_handler = None
    if debug_mode:
        debug_handler = logging.handlers.RotatingFileHandler(
            f"{log_dir}/{app_name}_debug.log",
            maxBytes=50*1024*1024,  # 50MB for debug
            backupCount=3
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(formatter)
    
    # Access log for API requests
    access_handler = logging.handlers.RotatingFileHandler(
        f"{log_dir}/{app_name}_access.log",
        maxBytes=10*1024*1024,
        backupCount=5
    )
    access_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(app_handler)
    root_logger.addHandler(error_handler)
    if debug_handler:
        root_logger.addHandler(debug_handler)
    
    # Configure specific loggers
    loggers_config = {
        'fastapi': log_level,
        'uvicorn': log_level,
        'uvicorn.access': logging.INFO,
        'uvicorn.error': logging.ERROR,
        'sqlalchemy': logging.WARNING,
        'asyncio': logging.WARNING,
        'motospect': log_level,
        'motospect.core': log_level,
        'motospect.sensors': log_level,
        'motospect.api': log_level,
        'motospect.mqtt': log_level,
        'motospect.obd': log_level,
        'motospect.fault': log_level,
    }
    
    for logger_name, level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
    
    # Special access logger
    access_logger = logging.getLogger('motospect.access')
    access_logger.addHandler(access_handler)
    access_logger.setLevel(logging.INFO)
    access_logger.propagate = False
    
    # Log startup information
    logger = logging.getLogger('motospect')
    logger.info("="*60)
    logger.info(f"MOTOSPECT Logging System Initialized")
    logger.info(f"Debug Mode: {debug_mode}")
    logger.info(f"Log Level: {logging.getLevelName(log_level)}")
    logger.info(f"Log Directory: {log_dir}")
    logger.info(f"JSON Format: {enable_json}")
    logger.info("="*60)
    
    return logger


class RequestLogger:
    """Middleware for logging HTTP requests"""
    
    def __init__(self, logger_name: str = 'motospect.access'):
        self.logger = logging.getLogger(logger_name)
    
    async def log_request(self, request, call_next):
        """Log incoming request and response"""
        start_time = datetime.now()
        
        # Generate request ID
        request_id = str(uuid.uuid4())[:8]
        
        # Log request
        self.logger.info(
            f"REQUEST [{request_id}] {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()
        
        # Log response
        self.logger.info(
            f"RESPONSE [{request_id}] {response.status_code} "
            f"in {duration:.3f}s"
        )
        
        return response


class PerformanceLogger:
    """Logger for performance metrics"""
    
    def __init__(self, logger_name: str = 'motospect.performance'):
        self.logger = logging.getLogger(logger_name)
    
    def log_timing(self, operation: str, duration: float, metadata: dict = None):
        """Log operation timing"""
        log_data = {
            'operation': operation,
            'duration_ms': duration * 1000,
            'timestamp': datetime.utcnow().isoformat()
        }
        if metadata:
            log_data.update(metadata)
        
        self.logger.info(f"TIMING: {operation} took {duration*1000:.2f}ms", extra=log_data)
    
    def log_metric(self, metric_name: str, value: float, unit: str = None, metadata: dict = None):
        """Log a metric value"""
        log_data = {
            'metric': metric_name,
            'value': value,
            'unit': unit,
            'timestamp': datetime.utcnow().isoformat()
        }
        if metadata:
            log_data.update(metadata)
        
        self.logger.info(f"METRIC: {metric_name}={value}{unit or ''}", extra=log_data)


# Context manager for timed operations
import time
from contextlib import contextmanager

@contextmanager
def log_timing(operation: str, logger=None):
    """Context manager to log operation timing"""
    if logger is None:
        logger = logging.getLogger('motospect.performance')
    
    start = time.time()
    logger.debug(f"Starting: {operation}")
    
    try:
        yield
    finally:
        duration = time.time() - start
        logger.info(f"Completed: {operation} in {duration*1000:.2f}ms")


# Decorator for function logging
import functools

def log_function(level=logging.DEBUG):
    """Decorator to log function calls"""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            logger.log(level, f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
            try:
                result = await func(*args, **kwargs)
                logger.log(level, f"{func.__name__} returned successfully")
                return result
            except Exception as e:
                logger.error(f"{func.__name__} raised exception: {e}", exc_info=True)
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            logger.log(level, f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.log(level, f"{func.__name__} returned successfully")
                return result
            except Exception as e:
                logger.error(f"{func.__name__} raised exception: {e}", exc_info=True)
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
