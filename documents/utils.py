"""
Utility functions for document processing.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from documents.processor import create_document_processor
from logger.logger import get_logger

logger = get_logger("document_utils")


def initialize_document_collections(documents_root: str = "./documents",
                                  chroma_db_path: str = "./chroma_db") -> Dict[str, bool]:
    """
    Initialize all document collections from the documents directory.
    
    Args:
        documents_root: Root directory containing document folders
        chroma_db_path: Path to ChromaDB storage
        
    Returns:
        Dictionary with folder names as keys and success status as values
    """
    processor = create_document_processor(documents_root, chroma_db_path)
    return processor.process_all_folders()


def search_in_collection(collection_name: str, 
                        query: str, 
                        n_results: int = 5,
                        chroma_db_path: str = "./chroma_db") -> List[Dict[str, Any]]:
    """
    Search for documents in a specific collection.
    
    Args:
        collection_name: Name of the collection to search in
        query: Search query
        n_results: Number of results to return
        chroma_db_path: Path to ChromaDB storage
        
    Returns:
        List of search results with document content, metadata, and similarity scores
    """
    processor = create_document_processor(chroma_db_path=chroma_db_path)
    return processor.search_documents(collection_name, query, n_results)


def list_available_collections(chroma_db_path: str = "./chroma_db") -> List[str]:
    """
    List all available collections.
    
    Args:
        chroma_db_path: Path to ChromaDB storage
        
    Returns:
        List of collection names
    """
    processor = create_document_processor(chroma_db_path=chroma_db_path)
    return processor.list_collections()


def get_collection_statistics(collection_name: str, 
                            chroma_db_path: str = "./chroma_db") -> Dict[str, Any]:
    """
    Get statistics about a collection.
    
    Args:
        collection_name: Name of the collection
        chroma_db_path: Path to ChromaDB storage
        
    Returns:
        Dictionary with collection statistics
    """
    processor = create_document_processor(chroma_db_path=chroma_db_path)
    return processor.get_collection_info(collection_name)


def create_metadata_template(folder_path: str, 
                           collection_name: str,
                           description: str = "") -> str:
    """
    Create a metadata template for a new document folder.
    
    Args:
        folder_path: Path to the document folder
        collection_name: Name for the collection
        description: Description of the collection
        
    Returns:
        Path to the created metadata file
    """
    folder = Path(folder_path)
    
    # Get all PDF files in the folder
    pdf_files = list(folder.glob("*.pdf"))
    
    # Create metadata template
    metadata_content = f"""collection_name: "{collection_name}"
description: "{description}"
chunk_size: 1000
chunk_overlap: 200
metadata_fields:
  - field: "document_type"
    description: "Type of document"
    type: "string"
  - field: "date_created"
    description: "Date the document was created"
    type: "date"
  - field: "category"
    description: "Document category"
    type: "string"
  - field: "author"
    description: "Document author"
    type: "string"

documents:
"""
    
    # Add entries for each PDF file
    for pdf_file in pdf_files:
        metadata_content += f"""  - file: "{pdf_file.name}"
    metadata:
      document_type: "pdf"
      date_created: ""
      category: ""
      author: ""
      title: ""
      
"""
    
    # Write metadata file
    metadata_file = folder / "metadata.yaml"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        f.write(metadata_content)
    
    logger.info(f"Created metadata template at: {metadata_file}")
    return str(metadata_file)


def validate_metadata_file(metadata_path: str) -> Dict[str, Any]:
    """
    Validate a metadata file and return validation results.
    
    Args:
        metadata_path: Path to the metadata file
        
    Returns:
        Dictionary with validation results
    """
    import yaml
    
    metadata_file = Path(metadata_path)
    folder_path = metadata_file.parent
    
    validation_results = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'file_check': {}
    }
    
    try:
        # Load metadata
        with open(metadata_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        print(data)
        # Check required fields
        required_fields = ['collection_name', 'documents']
        for field in required_fields:
            if field not in data:
                validation_results['errors'].append(f"Missing required field: {field}")
                validation_results['valid'] = False
        
        # Check if documents exist
        if 'documents' in data:
            if data['documents'] is None:
                validation_results['errors'].append("Data without documents")
                validation_results['valid'] = False
            else:
                for doc in data['documents']:
                    if 'file' not in doc:
                        validation_results['errors'].append("Document entry missing 'file' field")
                        validation_results['valid'] = False
                        continue
                    
                    file_path = folder_path / doc['file']
                    validation_results['file_check'][doc['file']] = {
                        'exists': file_path.exists(),
                        'is_pdf': file_path.suffix.lower() == '.pdf'
                    }
                    
                    if not file_path.exists():
                        validation_results['errors'].append(f"File not found: {doc['file']}")
                        validation_results['valid'] = False
                    elif not file_path.suffix.lower() == '.pdf':
                        validation_results['warnings'].append(f"File is not a PDF: {doc['file']}")
            
                # Check for orphaned PDF files
                pdf_files = set(f.name for f in folder_path.glob("*.pdf"))
                metadata_files = set(doc['file'] for doc in data.get('documents', []))
                
                orphaned_files = pdf_files - metadata_files
                if orphaned_files:
                    validation_results['warnings'].append(f"PDF files not in metadata: {list(orphaned_files)}")
        
    except Exception as e:
        validation_results['valid'] = False
        validation_results['errors'].append(f"Error reading metadata file: {e}")
    
    return validation_results


def rebuild_collection(collection_name: str,
                      documents_root: str = "./documents",
                      chroma_db_path: str = "./chroma_db") -> bool:
    """
    Rebuild a specific collection by deleting and recreating it.
    
    Args:
        collection_name: Name of the collection to rebuild
        documents_root: Root directory containing document folders
        chroma_db_path: Path to ChromaDB storage
        
    Returns:
        True if successful, False otherwise
    """
    processor = create_document_processor(documents_root, chroma_db_path)
    
    # Delete existing collection
    if collection_name in processor.list_collections():
        logger.info(f"Deleting existing collection: {collection_name}")
        processor.delete_collection(collection_name)
    
    # Find the folder for this collection
    documents_path = Path(documents_root)
    target_folder = None
    
    for folder_path in documents_path.iterdir():
        if folder_path.is_dir():
            metadata_file = folder_path / "metadata.yaml"
            if metadata_file.exists():
                import yaml
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if data.get('collection_name') == collection_name:
                        target_folder = folder_path
                        break
    
    if not target_folder:
        logger.error(f"No folder found for collection: {collection_name}")
        return False
    
    # Process the folder
    return processor.process_folder(target_folder)


def get_document_preview(collection_name: str, 
                        document_id: str,
                        chroma_db_path: str = "./chroma_db") -> Optional[Dict[str, Any]]:
    """
    Get a preview of a specific document chunk.
    
    Args:
        collection_name: Name of the collection
        document_id: ID of the document chunk
        chroma_db_path: Path to ChromaDB storage
        
    Returns:
        Document preview or None if not found
    """
    processor = create_document_processor(chroma_db_path=chroma_db_path)
    
    try:
        collection = processor.chroma_client.get_collection(
            name=collection_name,
            embedding_function=processor._get_embedding_function()
        )
        
        results = collection.get(
            ids=[document_id],
            include=['documents', 'metadatas']
        )
        
        if results['documents']:
            return {
                'id': document_id,
                'content': results['documents'][0],
                'metadata': results['metadatas'][0]
            }
        
    except Exception as e:
        logger.error(f"Error getting document preview: {e}")
    
    return None

## TESTING FUNCTIONS
def create_example_metadata():
    """Create example metadata for testing."""
    print("Creating example metadata template...")
    
    # Create a test folder structure
    test_folder = Path("./documents/test_collection")
    test_folder.mkdir(exist_ok=True)
    
    # Create metadata template
    metadata_file = create_metadata_template(
        folder_path=str(test_folder),
        collection_name="test_collection",
        description="Test collection for demonstration"
    )
    
    print(f"Created metadata template: {metadata_file}")
    
    # Validate the metadata
    validation = validate_metadata_file(metadata_file)
    print(f"Validation results: {validation}")

def validate_existing_metadata():
    """Validate existing metadata files."""
    print("Validating existing metadata files...")
    
    documents_root = Path("./documents")
    
    for folder_path in documents_root.iterdir():
        if folder_path.is_dir():
            metadata_file = folder_path / "metadata.yaml"
            if metadata_file.exists():
                print(f"\nValidating: {metadata_file}")
                validation = validate_metadata_file(str(metadata_file))
                
                if validation['valid']:
                    print("   ✓ Valid")
                else:
                    print("   ✗ Invalid")
                    for error in validation['errors']:
                        print(f"     Error: {error}")
                
                if validation['warnings']:
                    for warning in validation['warnings']:
                        print(f"     Warning: {warning}")
