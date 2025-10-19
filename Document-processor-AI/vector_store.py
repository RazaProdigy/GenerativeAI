# implementation of vector store using REDIS
from langchain_redis import RedisVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_community.docstore.document import Document
import os
from dotenv import load_dotenv
load_dotenv()

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0") # Default Redis URL
INDEX_NAME = "genai_docs"

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small")

def add_documents(texts: list[str]):
    docs = [Document(page_content=text) for text in texts]
    RedisVectorStore.from_documents(
        docs,
        embeddings,
        redis_url=REDIS_URL,
        index_name=INDEX_NAME
    )

def get_vector_store():
    """Get the Redis vector store."""
    return RedisVectorStore(
        redis_url=REDIS_URL,
        index_name=INDEX_NAME,
        embeddings=embeddings
    )

def retrieve(query: str, k: int = 2) -> list[str]:
    """Retrieve documents similar to the query."""
    vector_store = get_vector_store()
    results = vector_store.similarity_search(query, k=k)
    return [d.page_content for d in results] # Convert Document to string

def retrieve_with_score(query: str, k: int = 2) -> list[tuple[str, float]]:
    """Retrieve documents with their similarity scores."""
    vector_store = get_vector_store()
    results = vector_store.similarity_search_with_score(query, k=k)
    return [(d.page_content, score) for d, score in results] # Convert Document to string