# RAG Question Generator

A multi-agent system for generating MCQ and fill-in-the-blank questions from PDF documents using Large Language Models (LLMs) and Retrieval Augmented Generation (RAG).

## Features

- **Multi-Agent Architecture**: Question Generator + Question Evaluator + Question Optimizer agents
- **Iterative Workflow**: Questions are optimized iteratively based on evaluation feedback until they meet quality standards
- **PDF Processing**: Extract text and table of contents from PDF files
- **Vector Storage**: ChromaDB with OpenAI embeddings for efficient document retrieval
- **LLM Integration**: OpenAI GPT-3.5-turbo for question generation, evaluation, and optimization
- **Question Types**: Multiple Choice Questions (MCQ) and Fill-in-the-blank
- **Quality Control**: Automated evaluation and iterative optimization of generated questions
- **Max Iterations Control**: Configurable maximum iterations (default: 5) to prevent infinite loops
- **REST API**: FastAPI-based endpoints for easy integration
- **Docker Support**: Containerized deployment

## Architecture

```
PDF Upload → Text Extraction → Vector Storage → Question Generation → Question Evaluation
     ↓              ↓               ↓                    ↓                    ↓
   FastAPI    PDFProcessor    ChromaDB Vector    QuestionGenerator    QuestionEvaluator
                              (OpenAI Embeddings)        Agent              Agent
                                                                               ↓
                                                                    ┌─────────────────┐
                                                                    │  All Approved?  │
                                                                    │  or Max Iter?   │
                                                                    └────────┬────────┘
                                                                         Yes│  │No
                                                            ┌───────────────┘  └──────────┐
                                                            ↓                              ↓
                                                    Approved Questions          Question Optimizer
                                                                                         ↓
                                                                                Loop Back to Evaluation
```

### Iterative Workflow

The system now implements an **iterative optimization loop**:

1. **Generate**: Questions are generated based on retrieved context
2. **Evaluate**: Questions are evaluated against quality criteria (clarity, accuracy, educational value, etc.)
3. **Optimize**: If questions don't meet standards and max iterations not reached, they are sent to the optimizer
4. **Loop**: Optimized questions are re-evaluated (steps 2-3 repeat)
5. **Finalize**: Loop ends when either:
   - All questions are approved, OR
   - Maximum iterations (default: 5) is reached


## Installation

### Prerequisites

- Python 3.11
- OpenAI API key
- Docker (for containerized deployment)

### Local Setup

1. **Unzip the project folder:**
```bash
cd rag-question-generator
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

4. **Run the application:**
```bash
python -m rag_question_generator.main
```

### Docker Setup

1. **Build and run with Docker:**
```bash
docker build -t rag-question-generator .
docker run -p 8000:8000 -e OPENAI_API_KEY=your_api_key rag-question-generator
```

2. **Or use Docker Compose:**
```bash
# Set OPENAI_API_KEY in .env file
docker-compose up --build
```

## API Endpoints

### Health Check
```http
GET /health
```

### PDF Ingestion
```http
POST /ingest
Content-Type: multipart/form-data

file: <PDF file>
```

**Response:**
```json
{
  "success": true,
  "message": "PDF processed successfully",
  "table_of_contents": [...],
  "document_stats": {
    "filename": "document.pdf",
    "text_length": 15000,
    "num_chunks": 25,
    "document_ids": 25
  }
}
```

### Question Generation
```http
POST /generate/questions
Content-Type: application/json

{
  "concept": "machine learning",
  "query": "supervised learning algorithms",
  "question_types": ["mcq", "fill_blank"],
  "num_questions": 5,
  "max_iterations": 5
}
```

**Parameters:**
- `concept` (required): The main topic/concept for question generation
- `query` (optional): Specific query for document retrieval (defaults to concept)
- `question_types` (optional): Array of question types - "mcq" and/or "fill_blank" (default: ["mcq", "fill_blank"])
- `num_questions` (optional): Number of questions to generate (default: 5, range: 1-20)
- `max_iterations` (optional): Maximum optimization iterations before finalizing (default: 5, range: 1-10)

**Response:**
```json
{
  "success": true,
  "message": "Questions generated successfully",
  "concept": "machine learning",
  "questions": [...],
  "evaluations": [...],
  "approved_questions": [...],
  "evaluation_summary": {
    "total": 5,
    "approved": 4,
    "approval_rate": 0.8,
    "average_score": 8.2
  },
  "workflow_status": {
    "status": "workflow_completed",
    "documents_retrieved": 5,
    "questions_generated": 5,
    "questions_approved": 4,
    "current_iteration": 3,
    "max_iterations": 5,
    "optimization_feedback": "..."
  }
}
```

## Usage Examples

### 1. Basic Usage

```python
import httpx

# Upload a PDF
with open("document.pdf", "rb") as f:
    files = {"file": ("document.pdf", f, "application/pdf")}
    response = httpx.post("http://localhost:8000/ingest", files=files)

# Generate questions with iterative optimization
request_data = {
    "concept": "artificial intelligence",
    "question_types": ["mcq"],
    "num_questions": 3,
    "max_iterations": 5  # Optional: defaults to 5
}
response = httpx.post("http://localhost:8000/generate/questions", json=request_data)
```

### 2. Using the Test Scripts

```bash
# Install httpx for testing
pip install httpx

# Run the API test script
python test_api.py

# Or test the iterative workflow directly
python test_iterative_workflow.py
```

The `test_iterative_workflow.py` script specifically tests the new iterative optimization feature, showing how questions are improved across multiple iterations.

## Multi-Agent Workflow

The system uses a sophisticated multi-agent workflow with iterative optimization:

1. **Document Retrieval**: Retrieves relevant text chunks from vector store
2. **Question Generation**: Agent generates questions based on retrieved content
3. **Question Evaluation**: Agent evaluates question quality and accuracy
4. **Decision Point**: 
   - If all questions approved OR max iterations reached → Finalize
   - Otherwise → Optimize questions
5. **Question Optimization**: Agent improves questions based on evaluation feedback
6. **Re-evaluation**: Optimized questions loop back to step 3
7. **Result Filtering**: Only approved questions are returned

This iterative approach ensures higher quality questions by allowing multiple refinement cycles.

### Evaluation Criteria

Questions are evaluated on:
- **Clarity** (0-10): Question clarity and readability
- **Difficulty Appropriateness** (0-10): Matches stated difficulty level
- **Content Accuracy** (0-10): Factual correctness vs source material
- **Educational Value** (0-10): Learning outcome effectiveness

**Approval Standards:**
- Questions must score ≥ 7.0 overall and ≥ 6.0 on each criterion to be approved
- Unapproved questions receive specific feedback and improvement suggestions
- The optimizer uses this feedback to refine questions in subsequent iterations

Minimum approval threshold: 7.0 overall score


### Customization

- **Vector Store**: Modify `utils/vector_store.py` for different databases
- **LLM Provider**: Update agent configurations for other providers
- **Question Types**: Extend agents for additional question formats
- **Evaluation Criteria**: Modify evaluator prompts and scoring

## Testing

Run the included test script:

```bash
python test_api.py
```

For comprehensive testing with a sample PDF:
1. Place a PDF file named `sample.pdf` in the project root
2. Run the test script




