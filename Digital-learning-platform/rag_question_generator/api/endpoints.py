"""FastAPI endpoints for the RAG question generator."""

import os
from datetime import datetime
from typing import List, Dict, Any
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .models import (
    IngestResponse, QuestionRequest, QuestionResponse, 
    ErrorResponse, HealthResponse, QuestionData, EvaluationResult
)
from ..utils.pdf_processor import PDFProcessor
from ..utils.vector_store import VectorStore
from ..graph.multi_agent_workflow import MultiAgentWorkflow


# Global components
pdf_processor = PDFProcessor()
vector_store = VectorStore()
workflow = MultiAgentWorkflow(vector_store)

# FastAPI app
app = FastAPI(
    title="RAG Question Generator",
    description="Multi-agent system for generating MCQ and fill-in-the-blank questions from PDF documents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with basic API information."""
    return {
        "message": "RAG Question Generator API",
        "version": "1.0.0",
        "endpoints": {
            "ingest": "POST /ingest - Upload and process PDF files",
            "generate": "POST /generate/questions - Generate questions from processed PDFs",
            "health": "GET /health - Health check"
        }
    }

    


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    vector_store_status = vector_store.get_collection_stats()
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        vector_store_status=vector_store_status,
        timestamp=datetime.now().isoformat()
    )


@app.post("/ingest", response_model=IngestResponse)
async def ingest_pdf(file: UploadFile = File(...)):
    """Upload and process a PDF file."""
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="File must be a PDF"
            )
        
        # Read file content
        pdf_content = await file.read()
        
        if len(pdf_content) == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file uploaded"
            )
        
        # Extract text and table of contents
        text = pdf_processor.extract_text_from_pdf(pdf_content)
        toc = pdf_processor.extract_table_of_contents(pdf_content)
        
        # Split text into chunks
        documents = pdf_processor.split_text_into_chunks(
            text,
            metadata={
                "filename": file.filename,
                "upload_time": datetime.now().isoformat()
            }
        )
        
        # Add documents to vector store
        doc_ids = vector_store.add_documents(documents)
        
        # Prepare response
        document_stats = {
            "filename": file.filename,
            "text_length": len(text),
            "num_chunks": len(documents),
            "document_ids": len(doc_ids),
            "processing_time": datetime.now().isoformat()
        }
        
        return IngestResponse(
            success=True,
            message="PDF processed successfully",
            table_of_contents=toc,
            document_stats=document_stats
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/generate/questions", response_model=QuestionResponse)
async def generate_questions(request: QuestionRequest):
    """Generate MCQ questions based on the PDF content."""
    try:
        
        # Validate request
        if not request.concept.strip():
            raise HTTPException(
                status_code=400,
                detail="Concept cannot be empty"
            )
        
        # Check if vector store has documents
        stats = vector_store.get_collection_stats()
        if stats.get("document_count", 0) == 0:
            raise HTTPException(
                status_code=400,
                detail="No documents found. Please upload a PDF first using the /ingest endpoint."
            )
        
        # Run the multi-agent workflow with iterative optimization
        workflow_result = workflow.run_workflow(
            concept=request.concept,
            query=request.query,
            question_types=request.question_types,
            num_questions=request.num_questions,
            max_iterations=request.max_iterations
        )
        
        # Convert results to API models
        questions = [
            QuestionData(
                question=q.question,
                question_type=q.question_type,
                options=q.options,
                correct_answer=q.correct_answer,
                explanation=q.explanation,
                difficulty=q.difficulty,
                topic=q.topic
            )
            for q in workflow_result.get("generated_questions", [])
        ]
        
        evaluations = [
            EvaluationResult(
                question_id=e.question_id,
                overall_score=e.overall_score,
                clarity_score=e.clarity_score,
                difficulty_appropriateness=e.difficulty_appropriateness,
                content_accuracy=e.content_accuracy,
                educational_value=e.educational_value,
                feedback=e.feedback,
                is_approved=e.is_approved,
                improvements=e.improvements
            )
            for e in workflow_result.get("evaluations", [])
        ]
        
        approved_questions = [
            QuestionData(
                question=q.question,
                question_type=q.question_type,
                options=q.options,
                correct_answer=q.correct_answer,
                explanation=q.explanation,
                difficulty=q.difficulty,
                topic=q.topic
            )
            for q in workflow_result.get("approved_questions", [])
        ]
        
        workflow_status = workflow.get_workflow_status(workflow_result)
        
        return QuestionResponse(
            success=True,
            message="Questions generated successfully",
            concept=request.concept,
            questions=questions,
            evaluations=evaluations,
            approved_questions=approved_questions,
            evaluation_summary=workflow_result.get("evaluation_summary", {}),
            workflow_status=workflow_status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Environment setup
if os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
else:
    print("Warning: OPENAI_API_KEY not set. LLM functionality may not work.") 