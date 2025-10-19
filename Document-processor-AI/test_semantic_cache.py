"""
Demo script to test semantic caching functionality.
Shows how semantically similar questions can hit the cache even with different wording.
"""

import logging
import time
from cache_store import get as cache_get, set as cache_set
from config import CACHE_SIMILARITY_THRESHOLD

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def test_semantic_cache():
    """Test semantic caching with similar questions."""
    
    print("\n" + "="*80)
    print("SEMANTIC CACHE DEMO")
    print("="*80)
    print(f"Similarity Threshold: {CACHE_SIMILARITY_THRESHOLD}")
    print("="*80 + "\n")
    
    # Original question and answer
    original_question = "What is Agentic AI?"
    answer = "Agentic AI refers to AI systems that can act autonomously to achieve goals."
    
    # Cache the original question
    print(f"1. Caching original question: '{original_question}'")
    cache_set(original_question, answer, ttl=3600)
    print(f"   ✓ Cached successfully\n")
    
    time.sleep(1)  # Small delay to ensure cache is set
    
    # Test cases: similar questions that should hit the cache
    similar_questions = [
        "What is Agentic AI?",           # Exact match
        "what is agentic ai?",           # Different case
        "What is Agentic AI ?",          # Extra space
        "What's Agentic AI?",            # Contraction
        "Can you explain Agentic AI?",   # Different phrasing
        "Tell me about Agentic AI",      # Different structure
        "What does Agentic AI mean?",    # Semantic similarity
    ]
    
    print("2. Testing cache retrieval with similar questions:\n")
    
    for i, question in enumerate(similar_questions, 1):
        print(f"   Test {i}: '{question}'")
        cached_result = cache_get(question, similarity_threshold=CACHE_SIMILARITY_THRESHOLD)
        
        if cached_result:
            print(f"   ✓ CACHE HIT - Retrieved answer")
        else:
            print(f"   ✗ CACHE MISS - No similar question found above threshold")
        print()
    
    # Test with a completely different question
    print("3. Testing with unrelated question:\n")
    different_question = "What is the weather today?"
    print(f"   '{different_question}'")
    cached_result = cache_get(different_question, similarity_threshold=CACHE_SIMILARITY_THRESHOLD)
    
    if cached_result:
        print(f"   ✓ CACHE HIT (unexpected)")
    else:
        print(f"   ✗ CACHE MISS (expected - different topic)")
    
    print("\n" + "="*80)
    print("DEMO COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    test_semantic_cache()

