#!/usr/bin/env python3
"""Simple script to run the RAG Question Generator application."""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY environment variable not set.")
        print("LLM functionality will not work without a valid API key.")
        print("Set it with: export OPENAI_API_KEY=your_api_key")
        print()
    
    # Import and run the application
    try:
        from rag_question_generator.main import app
        import uvicorn
        
        print("Starting RAG Question Generator...")
        print("API will be available at: http://localhost:8000")
        print("Documentation at: http://localhost:8000/docs")
        print("Press Ctrl+C to stop")
        print()
        
        uvicorn.run(
            "rag_question_generator.api.endpoints:app",
            host="0.0.0.0",
            port=8000,
            reload=True
        )
    except ImportError as e:
        print(f"Error importing modules: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
    except Exception as e:
        print(f"Error starting application: {e}") 