# central configuration for the pipeline
import os
from dotenv import load_dotenv

load_dotenv()

# Environment variables
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")

# Model
DEFAULT_MODEL = "gpt-4.1-nano"
TEMPERATURE = 0.2
MAX_TOKENS = 512

# Cache 
CACHE_TTL_SECONDS = 1800 # 30 minutes
CACHE_SIMILARITY_THRESHOLD = 0.90  # Minimum cosine similarity for cache hit (0-1 scale)
VECTOR_TOP_K = 2  # number of top results to retrieve