# Semantic Cache Implementation

## Overview

This project now implements **semantic caching** using vector embeddings to cache and retrieve question-answer pairs based on semantic similarity rather than exact string matching.

## How It Works

### Traditional Caching (Before)
- Questions stored as exact strings
- Cache hit only when question is **word-for-word identical**
- Case-sensitive, whitespace-sensitive
- Example: "What is AI?" ≠ "what is ai?"

### Semantic Caching (Now)
- Questions converted to vector embeddings using OpenAI's `text-embedding-3-small`
- Cache hit when question is **semantically similar** (above threshold)
- Case-insensitive, whitespace-insensitive
- Works with rephrased questions
- Example: "What is AI?" ≈ "Can you explain AI?" ≈ "Tell me about AI"

## Architecture

```
User Question
     ↓
Generate Embedding (text-embedding-3-small)
     ↓
Search Cached Embeddings
     ↓
Calculate Cosine Similarity
     ↓
Similarity ≥ Threshold? 
     ↓
Yes → Return Cached Answer (Cache Hit)
No  → Process Pipeline → Generate Answer → Cache with Embedding
```

## Key Components

### 1. Embedding Generation
```python
def _get_embedding(text: str) -> list[float]:
    """Generate embedding using OpenAI text-embedding-3-small model."""
```

### 2. Similarity Calculation
```python
def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Calculate cosine similarity between two embedding vectors."""
```

### 3. Cache Storage Format
Each cached item stores:
```json
{
  "question": "Original question text",
  "embedding": [0.123, 0.456, ...],  // 1536-dimensional vector
  "answer": "Cached answer"
}
```

### 4. Cache Retrieval
- Generates embedding for incoming question
- Compares with all cached question embeddings
- Returns answer if best match exceeds threshold

## Configuration

In `config.py`:

```python
CACHE_SIMILARITY_THRESHOLD = 0.95  # Range: 0.0 to 1.0
```

### Threshold Guidelines

| Threshold | Behavior | Use Case |
|-----------|----------|----------|
| 0.99-1.0  | Very strict - almost exact matches only | High accuracy requirements |
| 0.95-0.98 | **Recommended** - semantically similar questions | Balanced approach |
| 0.90-0.94 | Moderate - catches more variations | Higher cache hit rate |
| 0.80-0.89 | Loose - may cache unrelated questions | Testing/debugging |

## Examples

### Cache Hit Examples (at 0.95 threshold)

| Original Question | Similar Questions (Will Hit Cache) |
|-------------------|-------------------------------------|
| "What is Agentic AI?" | - "what is agentic ai?" |
|                       | - "Can you explain Agentic AI?" |
|                       | - "Tell me about Agentic AI" |
|                       | - "What does Agentic AI mean?" |

### Cache Miss Examples

| Cached Question | Different Question (Will Miss) |
|-----------------|--------------------------------|
| "What is Agentic AI?" | "What is the weather today?" |
| "How do transformers work?" | "What is a neural network?" |

## Benefits

✅ **Higher Cache Hit Rate**: Questions don't need exact wording
✅ **User-Friendly**: Natural language variations are handled
✅ **Cost Savings**: Reduces LLM API calls
✅ **Lower Latency**: Cached responses return immediately
✅ **Flexible**: Adjustable similarity threshold

## Performance Considerations

### Pros
- More intelligent caching
- Better user experience
- Reduced API costs

### Cons
- Requires embedding API call for cache lookup (~5-10ms)
- O(n) search through cached items (can be optimized with vector database)
- Small storage overhead for embeddings

### Optimization Opportunities
For large-scale production:
1. Use Redis with vector search (RedisSearch)
2. Implement approximate nearest neighbor (ANN) algorithms
3. Add embedding cache to avoid re-embedding same questions
4. Use batch embedding for better throughput

## Testing

Run the semantic cache demo:

```bash
python test_semantic_cache.py
```

This will demonstrate:
1. Caching an original question
2. Testing various similar phrasings
3. Verifying unrelated questions miss the cache

## Dependencies

Added to `requirements.txt`:
- `numpy` - For vector operations and cosine similarity
- `openai>=1.0.0` - For embedding generation (already present)
- `redis==5.0.4` - For cache storage (already present)

## Environment Variables

Required in `.env`:
```
OPENAI_API_KEY=your_api_key_here
REDIS_URL=redis://localhost:6379/0
```

## Migration from Old Cache

The new semantic cache uses a different key prefix (`genai:semantic_cache:*` vs `genai:cache:*`), so:
- Old cached items won't interfere
- No migration needed
- Can run both systems in parallel if needed

## Monitoring

The semantic cache logs:
- Cache hits with similarity scores
- Near-misses (similar but below threshold)
- Embedding generation failures

Check logs for:
```
INFO - Semantic cache hit! Similarity: 0.9723
INFO - Similar question found but below threshold. Similarity: 0.9234 < 0.95
```

## Future Enhancements

1. **Vector Database Integration**: Use Redis Vector Similarity Search
2. **Cache Analytics**: Track cache hit rates and popular questions
3. **Dynamic Threshold**: Adjust based on query type or user preferences
4. **Multi-language Support**: Cache across different languages
5. **Cache Warming**: Pre-populate with common questions

