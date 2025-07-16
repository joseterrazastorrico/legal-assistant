"""
Documents module for Legal Assistant.

This module provides functionality for:
- Processing PDF documents
- Extracting text and metadata
- Storing documents in ChromaDB vector database
- Searching and retrieving documents

Main components:
- DocumentProcessor: Main class for document processing
- Utility functions for common operations
- Metadata-driven configuration system
"""

from .processor import DocumentProcessor, create_document_processor
from .utils import (
    initialize_document_collections,
    search_in_collection,
    list_available_collections,
    get_collection_statistics,
    create_metadata_template,
    validate_metadata_file,
    rebuild_collection,
    get_document_preview,
    create_example_metadata,
    validate_existing_metadata
)

__all__ = [
    'DocumentProcessor',
    'create_document_processor',
    'initialize_document_collections',
    'search_in_collection',
    'list_available_collections',
    'get_collection_statistics',
    'create_metadata_template',
    'validate_metadata_file',
    'rebuild_collection',
    'get_document_preview',
    'create_example_metadata',
    'validate_existing_metadata',
]
