# logic for Retrieval
from vector_store import retrieve
from config import VECTOR_TOP_K

def retrieve_context(query: str, k: int = VECTOR_TOP_K) -> str:
    """
    Retrieve context from the vector store based on the query.
    
    Args:
        query (str): The query to search for.
        k (int): The number of top results to return.
    
    Returns:
        str: The retrieved context as a single string.
    """
    results = retrieve(query, k)
    return "\n".join(results) 
