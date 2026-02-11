# GenAI RAG Pipeline with Document Processing

A production-ready Retrieval-Augmented Generation (RAG) system that combines semantic search with large language models to provide accurate, context-aware responses while maintaining safety, performance, and observability.

## 🌟 Features

- **🔍 Semantic Search**: Vector similarity search using OpenAI embeddings and Redis vector store
- **🚀 High Performance**: Intelligent semantic caching with 30-minute TTL reduces latency and costs
- **🛡️ Safety First**: Built-in guardrails and PII detection/redaction for secure outputs
- **📊 Full Observability**: Prometheus metrics integration and comprehensive audit logging
- **🎯 Smart Routing**: Context-aware prompt engineering for optimal responses
- **⚡ Dual Interface**: Both FastAPI REST API and CLI interfaces
- **🔄 Scalable Architecture**: Redis-based storage for horizontal scaling
- **🧪 Fully Tested**: Comprehensive test suite for all components

## 📋 Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [CLI Interface](#cli-interface)
  - [REST API](#rest-api)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Monitoring](#monitoring)
- [Technology Stack](#technology-stack)
- [License](#license)

## 🏗️ Architecture

The system follows a modular pipeline architecture:

```
User Query → Cache Check → Vector Retrieval → Prompt Engineering → LLM Call → Post-processing → Guardrails → Response
                ↓                                                          ↓
           Redis Cache                                            Observability/Metrics
```

For a detailed architecture diagram and component breakdown, see [architecture_diagram.md](architecture_diagram.md).

### Key Components

- **Cache Store**: Semantic caching using Redis for fast response retrieval
- **Vector Store**: Redis-based vector database for document similarity search
- **Retrieval Engine**: Context retrieval from document corpus
- **Router**: Intelligent prompt building and model selection
- **LLM Client**: OpenAI GPT-4.1-nano integration
- **Post-processor**: PII redaction and output sanitization
- **Guardrails**: Content safety and compliance checks
- **Observability**: Prometheus metrics and structured logging

## 📦 Prerequisites

- Python 3.13+
- Docker (for Redis)
- OpenAI API key
- Conda (recommended) or venv

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Document-processor-AI
```

### 2. Create Python Environment

Using Conda (recommended):

```bash
conda create --prefix ./my_env python=3.13 -y
conda activate ./my_env
```

Or using venv:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Redis Vector Database

Run Redis Stack server with Docker:

```bash
docker run -d \
  --name genai-redis \
  -p 6379:6379 \
  redis/redis-stack-server:latest
```

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 6. Load Document Corpus

Load your PDF documents into the vector store:

```bash
python load_corpus.py
```

This will process documents from the corpus and create vector embeddings in Redis.

## ⚙️ Configuration

The system is configured through `config.py` and environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | Your OpenAI API key (required) |
| `DEFAULT_MODEL` | `gpt-4.1-nano` | LLM model to use |
| `TEMPERATURE` | `0.2` | LLM temperature (0-1) |
| `MAX_TOKENS` | `512` | Maximum tokens in response |
| `CACHE_TTL_SECONDS` | `1800` | Cache expiration time (30 min) |
| `CACHE_SIMILARITY_THRESHOLD` | `0.90` | Semantic cache similarity threshold |
| `VECTOR_TOP_K` | `2` | Number of documents to retrieve |

## 💻 Usage

### CLI Interface

Run the pipeline from the command line:

```bash
python main.py --question "What is Agentic AI?"
```

This will:
1. Start the Prometheus metrics server on port 8002
2. Process your question through the full pipeline
3. Display the response
4. Keep the metrics server running for monitoring

**Example Output:**

```
2024-02-12 10:30:45 - INFO - Starting pipeline for question: What is Agentic AI?
2024-02-12 10:30:45 - INFO - Retrieval latency: 145ms
2024-02-12 10:30:46 - INFO - LLM latency: 823ms
Response: Agentic AI refers to AI systems that can act autonomously...
Pipeline execution completed. Keeping the metrics server running...
```

### REST API

Start the FastAPI server:

```bash
python app.py
```

Or using uvicorn directly:

```bash
uvicorn app:app --host 0.0.0.0 --port 8001
```

The API will be available at `http://localhost:8001`

#### API Endpoints

##### **POST /ask** - Ask a Question

```bash
curl -X POST "http://localhost:8001/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is Agentic AI?",
    "user_id": "user123"
  }'
```

Response:

```json
{
  "answer": "Agentic AI refers to AI systems that can act autonomously...",
  "user_id": "user123"
}
```

##### **GET /** - Root Endpoint

```bash
curl http://localhost:8001/
```

##### **GET /health** - Health Check

```bash
curl http://localhost:8001/health
```

#### Interactive API Documentation

- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

## 🧪 Testing

Run the test suite:

```bash
# Test guardrails
python test_guardrails.py

# Test retrieval system
python test_retrieval.py

# Test semantic caching
python test_semantic_cache.py
```

Run all tests:

```bash
python -m pytest
```

## 📊 Monitoring

### Prometheus Metrics

Metrics are exposed on port 8002 and include:

- `retrieval_latency_ms`: Time taken for vector search (milliseconds)
- `llm_latency_ms`: Time taken for LLM API calls (milliseconds)
- `cache_hits_total`: Number of semantic cache hits
- `cache_misses_total`: Number of cache misses

Access metrics:

```bash
curl http://localhost:8002/metrics
```

### Logs

Application logs are written to:
- Console output (STDOUT)
- `pipeline.log` file

Logs include structured information about:
- Request/response pairs
- Latency measurements
- Cache hits/misses
- Retrieved context
- Applied guardrails



## 🚀 Performance Optimizations

1. **Semantic Caching**: Reduces redundant LLM calls for similar queries
2. **Vector Search**: Fast similarity search using Redis vector indexing
3. **Configurable Top-K**: Retrieve only relevant documents
4. **Connection Pooling**: Efficient Redis connection management
5. **Async Operations**: FastAPI async support for concurrent requests

## 📈 Scalability

The system is designed for horizontal scaling:

- **Stateless Design**: All state stored in Redis
- **Redis Clustering**: Support for Redis cluster mode
- **Load Balancing**: Multiple API instances can share Redis backend
- **Distributed Caching**: Shared cache across instances
- **Monitoring**: Prometheus integration for distributed metrics
