"""
Logging configuration for the Legal Assistant system.
"""

import sys
import logging
from typing import Optional
from pathlib import Path
import structlog
from structlog.stdlib import LoggerFactory
import colorlog

from config.settings import log_settings


class StructuredLogger:
    """Structured logger using structlog."""
    
    def __init__(self, name: str, level: str = "INFO", log_file: Optional[str] = None):
        self.name = name
        self.level = level
        self.log_file = log_file
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup structured logging configuration."""
        # Create log directory if it doesn't exist
        if self.log_file:
            log_dir = Path(self.log_file).parent
            log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        # Setup standard logging
        logging.basicConfig(
            level=getattr(logging, self.level.upper()),
            format="%(message)s",
            handlers=self._get_handlers()
        )
    
    def _get_handlers(self) -> list:
        """Get logging handlers."""
        handlers = []
        
        # Console handler with colors
        console_handler = colorlog.StreamHandler(sys.stdout)
        console_handler.setFormatter(
            colorlog.ColoredFormatter(
                '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        )
        handlers.append(console_handler)
        
        # File handler if specified
        if self.log_file:
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
            )
            handlers.append(file_handler)
        
        return handlers
    
    def get_logger(self, name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
        """Get a structured logger instance."""
        logger_name = name or self.name
        return structlog.get_logger(logger_name)


class SimpleLogger:
    """Simple logger using standard logging."""
    
    def __init__(self, name: str, level: str = "INFO", log_file: Optional[str] = None):
        self.name = name
        self.level = level
        self.log_file = log_file
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup simple logging configuration."""
        # Create log directory if it doesn't exist
        if self.log_file:
            log_dir = Path(self.log_file).parent
            log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, self.level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=self._get_handlers()
        )
    
    def _get_handlers(self) -> list:
        """Get logging handlers."""
        handlers = []
        
        # Console handler with colors
        console_handler = colorlog.StreamHandler(sys.stdout)
        console_handler.setFormatter(
            colorlog.ColoredFormatter(
                '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        )
        handlers.append(console_handler)
        
        # File handler if specified
        if self.log_file:
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
            )
            handlers.append(file_handler)
        
        return handlers
    
    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """Get a simple logger instance."""
        logger_name = name or self.name
        return logging.getLogger(logger_name)


_logger_instance = None

def configure_logging(config=None):
    """Configure logging system."""
    global _logger_instance
    
    if config is None:
        config = log_settings
    
    if config.format == "structured":
        logger_class = StructuredLogger
    else:
        logger_class = SimpleLogger
    
    _logger_instance = logger_class(
        name="legal_assistant",
        level=config.level,
        log_file=config.file
    )


def get_logger(name: Optional[str] = None):
    """Get a logger instance."""
    global _logger_instance
    
    if _logger_instance is None:
        configure_logging()
    
    return _logger_instance.get_logger(name)
