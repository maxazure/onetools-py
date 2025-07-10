"""Structured logging configuration with structlog and rich"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from rich.console import Console
from rich.logging import RichHandler

from app.core.config import LoggingConfig, settings


class OneToolsLogger:
    """OneTools structured logger"""
    
    def __init__(self, config: LoggingConfig):
        self.config = config
        self.console = Console()
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Setup structured logging"""
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                self._add_caller_info,
                structlog.processors.JSONRenderer() if self.config.format == "json"
                else structlog.dev.ConsoleRenderer(colors=True)
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
        # Configure standard library logging
        self._setup_stdlib_logging()
    
    def _setup_stdlib_logging(self) -> None:
        """Setup standard library logging"""
        # Clear existing handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        # Set log level
        log_level = getattr(logging, self.config.level)
        root_logger.setLevel(log_level)
        
        # Console handler
        if self.config.format == "console":
            console_handler = RichHandler(
                console=self.console,
                show_time=True,
                show_path=True,
                rich_tracebacks=True,
                tracebacks_show_locals=True
            )
        else:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(
                logging.Formatter('%(message)s')
            )
        
        console_handler.setLevel(log_level)
        root_logger.addHandler(console_handler)
        
        # File handler (if configured)
        if self.config.file_path:
            self._setup_file_handler(root_logger, log_level)
        
        # Configure third-party loggers
        self._configure_third_party_loggers()
    
    def _setup_file_handler(self, root_logger: logging.Logger, log_level: int) -> None:
        """Setup file logging handler"""
        log_path = Path(self.config.file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        from logging.handlers import RotatingFileHandler
        
        file_handler = RotatingFileHandler(
            filename=log_path,
            maxBytes=self._parse_file_size(self.config.max_file_size),
            backupCount=self.config.backup_count,
            encoding="utf-8"
        )
        
        file_handler.setLevel(log_level)
        file_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )
        
        root_logger.addHandler(file_handler)
    
    def _parse_file_size(self, size_str: str) -> int:
        """简化的文件大小解析 - 固定为10MB"""
        # 简化为固定值，避免复杂的字符串解析
        return 10 * 1024 * 1024  # 10MB
    
    def _configure_third_party_loggers(self) -> None:
        """简化的第三方库日志配置"""
        # 仅配置必要的日志级别
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
        logging.getLogger('uvicorn').setLevel(logging.INFO)
        logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    @staticmethod
    def _add_caller_info(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
        """简化的调用者信息 - 仅添加日志级别"""
        # 简化为仅保留基本信息，避免复杂的栈帧检查
        return event_dict
    
    def get_logger(self, name: str) -> structlog.BoundLogger:
        """Get a structured logger instance"""
        return structlog.get_logger(name)


# Global logger instance
_logger_instance: Optional[OneToolsLogger] = None


def setup_logging(config: Optional[LoggingConfig] = None) -> OneToolsLogger:
    """Setup logging configuration"""
    global _logger_instance
    
    if config is None:
        config = settings.logging
    
    _logger_instance = OneToolsLogger(config)
    return _logger_instance


def get_logger(name: str = "onetools") -> structlog.BoundLogger:
    """Get a structured logger instance"""
    global logger
    
    if _logger_instance is None:
        setup_logging()
    
    # Initialize module-level logger if not already done
    if logger is None and name == __name__:
        logger = _logger_instance.get_logger(__name__)
    
    return _logger_instance.get_logger(name)


# Module-level logger will be created lazily
logger = None


class LoggerMixin:
    """Mixin class to add logging capabilities to any class"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = get_logger(self.__class__.__module__)
    
    def log_info(self, message: str, **kwargs) -> None:
        """Log info message"""
        self.logger.info(message, **kwargs)
    
    def log_warning(self, message: str, **kwargs) -> None:
        """Log warning message"""
        self.logger.warning(message, **kwargs)
    
    def log_error(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        """Log error message"""
        if error:
            kwargs['error'] = str(error)
            kwargs['error_type'] = type(error).__name__
        self.logger.error(message, **kwargs)
    
    def log_debug(self, message: str, **kwargs) -> None:
        """Log debug message"""
        self.logger.debug(message, **kwargs)


def log_execution_time(func_name: str):
    """简化的执行时间装饰器 - 仅记录基本信息"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            try:
                result = await func(*args, **kwargs)
                logger.info(f"Completed {func_name}")
                return result
            except Exception as e:
                logger.error(f"Failed {func_name}", error=str(e))
                raise
        
        def sync_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            try:
                result = func(*args, **kwargs)
                logger.info(f"Completed {func_name}")
                return result
            except Exception as e:
                logger.error(f"Failed {func_name}", error=str(e))
                raise
        
        import asyncio
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator