"""Main application entry point for the RAG Question Generator."""

import uvicorn
from rag_question_generator.api.endpoints import app

if __name__ == "__main__":
    uvicorn.run(
        "rag_question_generator.api.endpoints:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
