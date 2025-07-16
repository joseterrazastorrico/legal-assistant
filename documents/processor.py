"""
Document processor module for Legal Assistant.
Handles document extraction, processing, and vector storage using ChromaDB.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

import chromadb
from chromadb.config import Settings
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

from agents.llm import embeddings
from logger.logger import get_logger

IGNORED_FOLDERS = {
        '__pycache__',
        '.git',
        '.vscode',
        '.idea',
        'node_modules',
        '.pytest_cache',
        '.mypy_cache',
        'venv',
        'env',
        '.env',
        'dist',
        'build',
        'egg-info',
        '.DS_Store',
        'Thumbs.db'
    }

@dataclass
class DocumentMetadata:
    """Metadata for a document."""
    file: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CollectionConfig:
    """Configuration for a document collection."""
    collection_name: str
    description: str
    chunk_size: int = 1000
    chunk_overlap: int = 200
    metadata_fields: List[Dict[str, str]] = field(default_factory=list)
    documents: List[DocumentMetadata] = field(default_factory=list)


class DocumentProcessor:
    """Main document processor class."""
    
    def __init__(self, 
                 documents_root: str = "./documents",
                 chroma_db_path: str = "./chroma_db",
                 embedding_model=None):
        """
        Initialize the document processor.
        
        Args:
            documents_root: Root directory containing document folders
            chroma_db_path: Path to ChromaDB storage
            embedding_model: Embedding model to use (defaults to global embeddings)
        """
        self.documents_root = Path(documents_root)
        self.chroma_db_path = Path(chroma_db_path)
        self.embedding_model = embedding_model or embeddings
        self.logger = get_logger("document_processor")
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.chroma_db_path),
            settings=Settings(anonymized_telemetry=False,
                            allow_reset=True,
                            is_persistent=True )
            )
        
        # Initialize text splitter (will be configured per collection)
        self.text_splitter = None
        
    def _load_metadata(self, folder_path: Path) -> Optional[CollectionConfig]:
        """Load metadata configuration from a folder."""
        metadata_file = folder_path / "metadata.yaml"
        
        if not metadata_file.exists():
            self.logger.warning(f"No metadata.yaml found in {folder_path}")
            return None
            
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
            # Parse documents metadata
            documents = []
            for doc_data in data.get('documents', []):
                documents.append(DocumentMetadata(
                    file=doc_data['file'],
                    metadata=doc_data.get('metadata', {})
                ))
                
            return CollectionConfig(
                collection_name=data['collection_name'],
                description=data.get('description', ''),
                chunk_size=data.get('chunk_size', 1000),
                chunk_overlap=data.get('chunk_overlap', 200),
                metadata_fields=data.get('metadata_fields', []),
                documents=documents
            )
            
        except Exception as e:
            self.logger.error(f"Error loading metadata from {metadata_file}: {e}")
            return None
    
    def _extract_text_from_pdf(self, pdf_path: Path) -> List[Document]:
        """Extract text from PDF file."""
        try:
            loader = PyPDFLoader(str(pdf_path))
            documents = loader.load()
            self.logger.info(f"Extracted {len(documents)} pages from {pdf_path.name}")
            return documents
        except Exception as e:
            self.logger.error(f"Error extracting text from {pdf_path}: {e}")
            return []
    
    def _split_documents(self, documents: List[Document], config: CollectionConfig) -> List[Document]:
        """Split documents into chunks."""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunks = self.text_splitter.split_documents(documents)
        self.logger.info(f"Split {len(documents)} documents into {len(chunks)} chunks")
        return chunks
    
    def _create_or_get_collection(self, config: CollectionConfig):
        """Create or get existing ChromaDB collection."""
        try:
            # Try to get existing collection
            collection = self.chroma_client.get_collection(
                name=config.collection_name,
                embedding_function=self._get_embedding_function()
            )
            self.logger.info(f"Retrieved existing collection: {config.collection_name}")
            
        except Exception:
            # Create new collection if it doesn't exist
            collection = self.chroma_client.create_collection(
                name=config.collection_name,
                embedding_function=self._get_embedding_function(),
                metadata={"description": config.description}
            )
            self.logger.info(f"Created new collection: {config.collection_name}")
            
        return collection
    
    def _get_embedding_function(self):
        """Get embedding function for ChromaDB."""
        class EmbeddingFunction:
            def __init__(self, model):
                self.model = model
                
            def __call__(self, input):
                if isinstance(input, str):
                    input = [input]
                return self.model.embed_documents(input)
        
        return EmbeddingFunction(self.embedding_model)
    
    def _add_documents_to_collection(self, collection, chunks: List[Document], 
                                   config: CollectionConfig, folder_path: Path):
        """Add document chunks to ChromaDB collection."""
        texts = []
        metadatas = []
        ids = []
        
        for i, chunk in enumerate(chunks):
            # Extract source file from chunk metadata
            source_file = Path(chunk.metadata.get('source', '')).name
            
            # Find document metadata for this file
            doc_metadata = {}
            for doc in config.documents:
                if doc.file == source_file:
                    doc_metadata = doc.metadata.copy()
                    break
            
            # Add chunk-specific metadata
            chunk_metadata = {
                'source': source_file,
                'chunk_index': i,
                'collection': config.collection_name,
                'folder_path': str(folder_path),
                **doc_metadata,
                **chunk.metadata
            }
            
            texts.append(chunk.page_content)
            metadatas.append(chunk_metadata)
            ids.append(f"{config.collection_name}_{source_file}_{i}")
        
        # Add to collection
        collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        self.logger.info(f"Added {len(chunks)} chunks to collection {config.collection_name}")
    
    def process_folder(self, folder_path: Path) -> bool:
        """Process a single folder containing documents."""
        self.logger.info(f"Processing folder: {folder_path}")
        
        # Load metadata configuration
        config = self._load_metadata(folder_path)
        if not config:
            self.logger.info(f"No valid metadata found in {folder_path}")
            return False
        
        # Create or get collection
        collection = self._create_or_get_collection(config)
        
        # Process each document
        all_documents = []
        for doc_metadata in config.documents:
            pdf_path = folder_path / doc_metadata.file
            
            if not pdf_path.exists():
                self.logger.warning(f"Document not found: {pdf_path}")
                continue
            
            # Extract text from PDF
            documents = self._extract_text_from_pdf(pdf_path)
            if documents:
                all_documents.extend(documents)
        
        if not all_documents:
            self.logger.warning(f"No documents processed in folder: {folder_path}")
            return False
        
        # Split documents into chunks
        chunks = self._split_documents(all_documents, config)
        
        # Add to ChromaDB collection
        self._add_documents_to_collection(collection, chunks, config, folder_path)
        
        return True
    
    def process_all_folders(self) -> Dict[str, bool]:
        """Process all folders in the documents directory."""
        results = {}
        
        if not self.documents_root.exists():
            self.logger.error(f"Documents root directory not found: {self.documents_root}")
            return results
        
        # Find all subdirectories
        for folder_path in self.documents_root.iterdir():
            if folder_path.is_dir():
                folder_name = folder_path.name

                # skip ignored folders
                if folder_name in IGNORED_FOLDERS:
                    self.logger.info(f"Skipping ignored folder: {folder_name}")
                    continue
                # skip hidden folders
                if folder_name.startswith('.'):
                    self.logger.info(f"Skipping hidden folder: {folder_name}")
                    continue

                # Process each folder
                self.logger.info(f"Processing folder: {folder_name}")
                
                try:
                    results[folder_name] = self.process_folder(folder_path)
                except Exception as e:
                    self.logger.error(f"Error processing folder {folder_name}: {e}")
                    results[folder_name] = False
        
        return results
    
    def list_collections(self) -> List[str]:
        """List all collections in ChromaDB."""
        collections = self.chroma_client.list_collections()
        return [col.name for col in collections]
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get information about a specific collection."""
        try:
            collection = self.chroma_client.get_collection(
                name=collection_name,
                embedding_function=self._get_embedding_function()
            )
            
            count = collection.count()
            return {
                'name': collection_name,
                'count': count,
                'metadata': collection.metadata
            }
        except Exception as e:
            self.logger.error(f"Error getting collection info for {collection_name}: {e}")
            return {}
    
    def search_documents(self, collection_name: str, query: str, 
                        n_results: int = 5) -> List[Dict[str, Any]]:
        """Search documents in a specific collection."""
        try:
            collection = self.chroma_client.get_collection(
                name=collection_name,
                embedding_function=self._get_embedding_function()
            )
            
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i]
                })
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Error searching in collection {collection_name}: {e}")
            return []
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection."""
        try:
            self.chroma_client.delete_collection(name=collection_name)
            self.logger.info(f"Deleted collection: {collection_name}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting collection {collection_name}: {e}")
            return False


def create_document_processor(documents_root: str = "./documents",
                            chroma_db_path: str = "./chroma_db") -> DocumentProcessor:
    """Factory function to create a document processor."""
    return DocumentProcessor(
        documents_root=documents_root,
        chroma_db_path=chroma_db_path
    )
