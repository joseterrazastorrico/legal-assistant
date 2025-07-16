from langchain_core.tools import tool
from documents.utils import search_in_collection
from config.settings import constants

@tool("retrieve_data", return_direct=False)
def retrieve_data(
    query: str,
    collection_name: str,
    n_results: int = constants.RAG_N_RESULTS,
) -> str:
    """Extracts relevant data from a collection based on the query."""
    results = search_in_collection(collection_name, query, n_results=n_results)
    outputs = []
    for result in results:
        if result['distance'] > constants.RAG_TRESHOLD_DISTANCES:
            if constants.RAG_EXTRACTED_METADATA is True:
                list_keys_metadata = constants.RAG_EXTRACTED_METADATA_KEYS
                outputs.append({
                    "metadata": {k:v for k, v in result['metadata'].items() if k in list_keys_metadata},
                    "content": result['document']
                })
            else:
                outputs.append({
                    "content": result['document']
                })
    return outputs