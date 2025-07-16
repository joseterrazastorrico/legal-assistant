from typing import Literal
from pydantic import BaseModel


class LoggingConfig(BaseModel):
    """Configuration for logging."""
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    format: Literal["structured", "simple"] = "structured"
    file: str = "./logs/legal_assistant.log"

log_settings = LoggingConfig()

## CONSTANTS
class Constants(BaseModel):
    """Constants used in the application."""
    RAG_TRESHOLD_DISTANCES: float = 0.3
    RAG_N_RESULTS: int = 3
    RAG_EXTRACTED_METADATA: bool = False
    RAG_EXTRACTED_METADATA_KEYS: list[str] = ["source", "page_label"]

constants = Constants()
