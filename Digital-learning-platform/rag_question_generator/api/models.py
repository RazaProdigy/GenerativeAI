"""Pydantic models for API request and response schemas."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class IngestResponse(BaseModel):
    """Response model for the ingest endpoint."""
    success: bool = Field(description="Whether the ingestion was successful")
    message: str = Field(description="Status message")
    table_of_contents: List[Dict[str, Any]] = Field(description="Extracted table of contents")
    document_stats: Dict[str, Any] = Field(description="Statistics about the processed document")


class QuestionRequest(BaseModel):
    """Request model for question generation."""
    concept: str = Field(description="The concept or topic to generate questions about")
    query: Optional[str] = Field(default=None, description="Optional specific query for retrieval")
    question_types: List[str] = Field(
        default=["mcq", "fill_blank"],
        description="Types of questions to generate: 'mcq' or 'fill_blank'"
    )
    num_questions: int = Field(default=5, ge=1, le=20, description="Number of questions to generate")
    max_iterations: int = Field(default=5, ge=1, le=10, description="Maximum optimization iterations before finalizing")


class QuestionData(BaseModel):
    """Model for a single question."""
    question: str = Field(description="The question text")
    question_type: str = Field(description="Type of question: 'mcq' or 'fill_blank'")
    options: Optional[List[str]] = Field(default=None, description="Options for MCQ questions")
    correct_answer: str = Field(description="The correct answer")
    explanation: str = Field(description="Explanation for the answer")
    difficulty: str = Field(description="Difficulty level: easy, medium, hard")
    topic: str = Field(description="Main topic/concept covered")


class EvaluationResult(BaseModel):
    """Model for question evaluation results."""
    question_id: Optional[str] = Field(default=None, description="Identifier for the question")
    overall_score: float = Field(description="Overall quality score (0-10)")
    clarity_score: float = Field(description="Clarity and readability score (0-10)")
    difficulty_appropriateness: float = Field(description="Appropriateness of difficulty level (0-10)")
    content_accuracy: float = Field(description="Accuracy relative to source content (0-10)")
    educational_value: float = Field(description="Educational value and learning outcome (0-10)")
    feedback: str = Field(description="Detailed feedback and suggestions for improvement")
    is_approved: bool = Field(description="Whether the question meets quality standards")
    improvements: List[str] = Field(default_factory=list, description="Specific improvement suggestions")


class QuestionResponse(BaseModel):
    """Response model for question generation."""
    success: bool = Field(description="Whether the generation was successful")
    message: str = Field(description="Status message")
    concept: str = Field(description="The concept the questions are about")
    questions: List[QuestionData] = Field(description="Generated questions")
    evaluations: List[EvaluationResult] = Field(description="Evaluation results for each question")
    approved_questions: List[QuestionData] = Field(description="Questions that met quality standards")
    evaluation_summary: Dict[str, Any] = Field(description="Summary of evaluation metrics")
    workflow_status: Dict[str, Any] = Field(description="Status of the multi-agent workflow")


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = Field(default=False, description="Always false for error responses")
    error: str = Field(description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(description="Service status")
    version: str = Field(description="API version")
    vector_store_status: Dict[str, Any] = Field(description="Vector store status")
    timestamp: str = Field(description="Response timestamp") 