#!/usr/bin/env python3
"""
Example script demonstrating the document processing module.
"""

import sys
from pathlib import Path
from documents import (
    initialize_document_collections,
    search_in_collection,
    list_available_collections,
    get_collection_statistics,
    validate_metadata_file,
    create_metadata_template
)
from logger.logger import get_logger

logger = get_logger("document_example")


def main():
    """Main example function."""
    print("=== Legal Assistant Document Processing Example ===\n")
    
    # 1. Initialize all document collections
    print("1. Initializing document collections...")
    results = initialize_document_collections()
    
    for folder_name, success in results.items():
        status = "✓" if success else "✗"
        print(f"   {status} {folder_name}")
    
    if not any(results.values()):
        print("   No collections were processed successfully.")
        return
    
    print()
    
    # 2. List available collections
    print("2. Available collections:")
    collections = list_available_collections()
    
    if not collections:
        print("   No collections found.")
        return
    
    for collection in collections:
        print(f"   - {collection}")
    
    print()
    
    # 3. Show collection statistics
    print("3. Collection statistics:")
    for collection in collections:
        stats = get_collection_statistics(collection)
        print(f"   Collection: {collection}")
        print(f"     Documents: {stats.get('count', 0)}")
        print(f"     Description: {stats.get('metadata', {}).get('description', 'N/A')}")
        print()
    
    # 4. Search example
    if collections:
        collection_name = collections[0]
        print(f"4. Searching in collection '{collection_name}':")
        
        # Example search queries
        queries = [
            "protección consumidor",
            "derechos del consumidor",
            "responsabilidad proveedor"
        ]
        
        for query in queries:
            print(f"   Query: '{query}'")
            results = search_in_collection(collection_name, query, n_results=2)
            
            if results:
                for i, result in enumerate(results, 1):
                    print(f"     Result {i} (similarity: {result['distance']:.3f}):")
                    print(f"       Source: {result['metadata'].get('source', 'Unknown')}")
                    print(f"       Content: {result['document'][:100]}...")
                    print()
            else:
                print("     No results found.")
            print()
    
    print("=== Example completed ===")


def create_example_metadata():
    """Create example metadata for testing."""
    print("Creating example metadata template...")
    
    # Create a test folder structure
    test_folder = Path("./documents/test_collection")
    test_folder.mkdir(exist_ok=True)
    
    # Create metadata template
    metadata_file = create_metadata_template(
        str(test_folder),
        "test_collection",
        "Test collection for demonstration"
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


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "create-template":
            create_example_metadata()
        elif sys.argv[1] == "validate":
            validate_existing_metadata()
        else:
            print("Usage: python example_usage.py [create-template|validate]")
    else:
        main()
