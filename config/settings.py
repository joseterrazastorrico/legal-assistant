import os
from typing import Literal, Optional
from pydantic import BaseModel, Field


class LoggingConfig(BaseModel):
    """Configuration for logging."""
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    format: Literal["structured", "simple"] = "structured"
    file: str = "./logs/legal_assistant.log"

log_settings = LoggingConfig()