"""Vector store utilities for document embeddings and retrieval.

This module uses OpenAI's embedding API for generating vector embeddings,
eliminating the need to download and store local embedding models.
"""

import os
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma


class VectorStore:
    """Handles vector storage and retrieval operations."""
    
    def __init__(self, 
                 collection_name: str = "pdf_documents", 
                 persist_directory: str = "./chroma_db",
                 embedding_model: str = "text-embedding-3-small"):
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        # Initialize OpenAI embeddings model
        # This uses the OpenAI API instead of downloading local models
        self.embeddings = OpenAIEmbeddings(
            model=embedding_model,
            # You can also specify other parameters like:
            # chunk_size=1000,  # Maximum number of texts to embed in each batch
            # max_retries=3,    # Number of retries for API calls
        )
        
        # Ensure directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize Chroma vector store
        self.vector_store = None
        self._initialize_vector_store()
    
    def _initialize_vector_store(self):
        """Initialize the Chroma vector store."""
        try:
            self.vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize vector store: {str(e)}")
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents to the vector store."""
        try:
            if not documents:
                raise ValueError("No documents provided")
            
            # Add documents to vector store
            doc_ids = self.vector_store.add_documents(documents)
            
            # Persistence is handled automatically in newer versions
            # self.vector_store.persist()  # No longer needed
            
            return doc_ids
        except Exception as e:
            raise RuntimeError(f"Failed to add documents to vector store: {str(e)}")
    
    def similarity_search(self, query: str, k: int = 4, score_threshold: float = 0.0) -> List[Document]:
        """Search for similar documents."""
        try:
            if not self.vector_store:
                raise RuntimeError("Vector store not initialized")
            
            # Perform similarity search
            results = self.vector_store.similarity_search_with_score(query, k=k)
            
            # Filter by score threshold
            filtered_results = [
                doc for doc, score in results 
                if score >= score_threshold
            ]
            
            return filtered_results
        except Exception as e:
            raise RuntimeError(f"Failed to perform similarity search: {str(e)}")
    
    def similarity_search_with_scores(self, query: str, k: int = 4) -> List[tuple]:
        """Search for similar documents with relevance scores."""
        try:
            if not self.vector_store:
                raise RuntimeError("Vector store not initialized")
            
            results = self.vector_store.similarity_search_with_score(query, k=k)
            return results
        except Exception as e:
            raise RuntimeError(f"Failed to perform similarity search with scores: {str(e)}")
    
    def get_retriever(self, search_type: str = "similarity", search_kwargs: Optional[Dict] = None):
        """Get a retriever for the vector store."""
        if search_kwargs is None:
            search_kwargs = {"k": 4}
        
        return self.vector_store.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs
        )
    
    def delete_collection(self):
        """Delete the entire collection."""
        try:
            if self.vector_store:
                self.vector_store.delete_collection()
                self._initialize_vector_store()
        except Exception as e:
            raise RuntimeError(f"Failed to delete collection: {str(e)}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        try:
            if not self.vector_store:
                return {"document_count": 0, "status": "not_initialized"}
            
            # Get collection info
            collection = self.vector_store._collection
            count = collection.count()
            
            return {
                "document_count": count,
                "collection_name": self.collection_name,
                "status": "initialized"
            }
        except Exception as e:
            return {"error": str(e), "status": "error"} 