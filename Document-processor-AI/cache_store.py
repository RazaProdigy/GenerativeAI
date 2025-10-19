# cache store logic with semantic similarity using embeddings

from typing import Optional
import os
import logging
import redis
import json
import numpy as np
from openai import OpenAI

USE_REDIS = False

try:
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    _client = redis.Redis.from_url(REDIS_URL)
    _client.ping()  # Check if Redis is available
    USE_REDIS = True
    logging.info(f"Redis is available and will be used for caching. {REDIS_URL}")

except Exception as e:
    logging.warning(f"Redis is not available: {e}. Caching will not be used.")
    USE_REDIS = False
    _client = {}

logging.info(f"Cache Backend: {'Redis' if USE_REDIS else 'In-Memory'}")

# Initialize OpenAI client for embeddings
_openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
EMBEDDING_MODEL = "text-embedding-3-small"

def _get_embedding(text: str) -> list[float]:
    """Generate embedding for the given text using OpenAI."""
    try:
        response = _openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logging.error(f"Error generating embedding: {e}")
        return None

def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    vec1_np = np.array(vec1)
    vec2_np = np.array(vec2)
    return np.dot(vec1_np, vec2_np) / (np.linalg.norm(vec1_np) * np.linalg.norm(vec2_np))

def _key(key: str) -> str:
    """Generate a cache key."""
    return f"genai:semantic_cache:{key}"

def get(question: str, similarity_threshold: float = 0.95) -> Optional[str]:
    """
    Get a value from the cache using semantic similarity.
    
    Args:
        question: The question to search for
        similarity_threshold: Minimum cosine similarity (0-1) for a cache hit
    
    Returns:
        The cached answer if a similar question is found, None otherwise
    """
    if not USE_REDIS:
        logging.warning("Redis is not available. Semantic caching is disabled.")
        return None
    
    # Generate embedding for the incoming question
    question_embedding = _get_embedding(question)
    if question_embedding is None:
        return None
    
    # Get all cached question keys
    cache_keys = _client.keys(_key("*"))
    
    if not cache_keys:
        return None
    
    best_match_score = -1
    best_match_answer = None
    
    # Search through all cached questions to find the most similar one
    for key in cache_keys:
        try:
            cached_data = _client.get(key)
            if not cached_data:
                continue
            
            cached_item = json.loads(cached_data.decode('utf-8'))
            cached_embedding = cached_item.get("embedding")
            cached_answer = cached_item.get("answer")
            
            if not cached_embedding or not cached_answer:
                continue
            
            # Calculate similarity
            similarity = _cosine_similarity(question_embedding, cached_embedding)
            
            if similarity > best_match_score:
                best_match_score = similarity
                best_match_answer = cached_answer
        
        except Exception as e:
            logging.error(f"Error processing cached item {key}: {e}")
            continue
    
    # Return the answer if similarity exceeds threshold
    if best_match_score >= similarity_threshold:
        logging.info(f"Semantic cache hit! Similarity: {best_match_score:.4f}")
        return best_match_answer
    elif best_match_score > 0:
        logging.info(f"Similar question found but below threshold. Similarity: {best_match_score:.4f} < {similarity_threshold}")
    
    return None

def set(question: str, answer: str, ttl: int = 3600) -> None:
    """
    Set a value in the cache with semantic embedding.
    
    Args:
        question: The question to cache
        answer: The answer to cache
        ttl: Time to live in seconds
    """
    if not USE_REDIS:
        logging.warning("Redis is not available. Semantic caching is disabled.")
        return
    
    # Generate embedding for the question
    question_embedding = _get_embedding(question)
    if question_embedding is None:
        logging.error("Failed to generate embedding for caching")
        return
    
    # Create a unique key using hash of the question
    import hashlib
    question_hash = hashlib.md5(question.encode()).hexdigest()
    key = _key(question_hash)
    
    # Store question, embedding, and answer together
    cache_data = {
        "question": question,
        "embedding": question_embedding,
        "answer": answer
    }
    
    _client.setex(key, ttl, json.dumps(cache_data))