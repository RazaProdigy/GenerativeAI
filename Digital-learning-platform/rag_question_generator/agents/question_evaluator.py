"""Question evaluator agent for assessing the quality of generated questions."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.language_models.llms import LLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from .question_generator import QuestionData
import json


class EvaluationResult(BaseModel):
    """Data model for question evaluation results."""
    question_id: Optional[str] = Field(default=None, description="Identifier for the question")
    overall_score: float = Field(description="Overall quality score (0-10)")
    clarity_score: float = Field(description="Clarity and readability score (0-10)")
    difficulty_appropriateness: float = Field(description="Appropriateness of difficulty level (0-10)")
    content_accuracy: float = Field(description="Accuracy relative to source content (0-10)")
    educational_value: float = Field(description="Educational value and learning outcome (0-10)")
    feedback: str = Field(description="Detailed feedback and suggestions for improvement")
    is_approved: bool = Field(description="Whether the question meets quality standards")
    improvements: List[str] = Field(default_factory=list, description="Specific improvement suggestions")


class QuestionEvaluatorAgent:
    """Agent responsible for evaluating the quality of generated questions."""
    
    def __init__(self, llm: Optional[LLM] = None, temperature: float = 0.3):
        # Use lower temperature for more consistent evaluation
        self.llm = llm or ChatOpenAI(
            model="gpt-4o-mini",
            temperature=temperature
        )
        
        self.evaluation_prompt = PromptTemplate(
            input_variables=["questions", "source_context"],
            template="""
You are an expert educational content evaluator. Your task is to assess the quality of generated questions based on the provided source context.

Source Context:
{source_context}

Questions to Evaluate:
{questions}

Evaluation Criteria:
1. Clarity (0-10): Is the question clear, unambiguous, and well-written?
2. Difficulty Appropriateness (0-10): Does the stated difficulty match the actual cognitive load?
3. Content Accuracy (0-10): Is the question factually correct and aligned with source content?
4. Educational Value (0-10): Does the question promote meaningful learning?
5. Technical Quality (0-10): Are options well-constructed, answers correct, explanations adequate?

For each question, provide a detailed evaluation in JSON format:

{{
    "evaluations": [
        {{
            "question_id": "Q1",
            "overall_score": 8.5,
            "clarity_score": 9.0,
            "difficulty_appropriateness": 8.0,
            "content_accuracy": 9.0,
            "educational_value": 8.0,
            "feedback": "Detailed analysis of strengths and weaknesses",
            "is_approved": true,
            "improvements": ["Specific suggestion 1", "Specific suggestion 2"]
        }}
    ]
}}

Quality Standards:
- Minimum overall score of 7.0 for approval
- All individual scores should be >= 6.0
- Must be factually accurate and pedagogically sound
- Options should be plausible but clearly distinguishable

Evaluate all questions:
"""
        )
        
        self.evaluation_chain = self.evaluation_prompt | self.llm
    
    def evaluate_questions(
        self,
        questions: List[QuestionData],
        source_context: str
    ) -> List[EvaluationResult]:
        """Evaluate a list of questions against quality criteria."""
        
        if not questions:
            return []
        
        # Prepare questions for evaluation
        questions_text = self._format_questions_for_evaluation(questions)
        
        try:
            # Get evaluation from LLM
            response = self.evaluation_chain.invoke({
                "questions": questions_text,
                "source_context": source_context[:3000]  # Limit context to avoid token limits
            })
            
            # Parse evaluation results (extract content from message object)
            response_content = response.content if hasattr(response, 'content') else str(response)
            evaluation_data = self._parse_evaluation_response(response_content)
            
            # Create EvaluationResult objects
            results = []
            for i, eval_data in enumerate(evaluation_data.get("evaluations", [])):
                try:
                    # Add question_id if not present
                    if "question_id" not in eval_data:
                        eval_data["question_id"] = f"Q{i+1}"
                    
                    result = EvaluationResult(**eval_data)
                    results.append(result)
                except Exception as e:
                    print(f"Error creating evaluation result for question {i}: {e}")
            
            return results
            
        except Exception as e:
            print(f"Error during evaluation: {e}")
            return self._create_fallback_evaluations(questions)
    
    def _format_questions_for_evaluation(self, questions: List[QuestionData]) -> str:
        """Format questions for evaluation prompt."""
        formatted = []
        
        for i, q in enumerate(questions, 1):
            question_text = f"Question {i}:\n"
            question_text += f"Type: {q.question_type}\n"
            question_text += f"Question: {q.question}\n"
            
            if q.options:
                question_text += f"Options: {', '.join(q.options)}\n"
            
            question_text += f"Correct Answer: {q.correct_answer}\n"
            question_text += f"Explanation: {q.explanation}\n"
            question_text += f"Difficulty: {q.difficulty}\n"
            question_text += f"Topic: {q.topic}\n"
            
            formatted.append(question_text)
        
        return "\n\n".join(formatted)
    
    def _parse_evaluation_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON evaluation response from LLM."""
        try:
            # Clean the response
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            
            # Parse JSON
            evaluation_data = json.loads(cleaned_response.strip())
            return evaluation_data
            
        except json.JSONDecodeError as e:
            print(f"Error parsing evaluation response: {e}")
            print(f"Response: {response}")
            return {"evaluations": []}
    
    def _create_fallback_evaluations(self, questions: List[QuestionData]) -> List[EvaluationResult]:
        """Create basic evaluations when LLM evaluation fails."""
        results = []
        
        for i, question in enumerate(questions):
            # Basic evaluation based on question structure
            clarity_score = 8.0 if question.question and len(question.question) > 10 else 6.0
            content_accuracy = 7.0  # Default assumption
            educational_value = 7.0 if question.explanation else 6.0
            
            if question.question_type == "mcq":
                difficulty_score = 8.0 if question.options and len(question.options) == 4 else 6.0
            else:
                difficulty_score = 7.0
            
            overall_score = (clarity_score + content_accuracy + educational_value + difficulty_score) / 4
            
            result = EvaluationResult(
                question_id=f"Q{i+1}",
                overall_score=overall_score,
                clarity_score=clarity_score,
                difficulty_appropriateness=difficulty_score,
                content_accuracy=content_accuracy,
                educational_value=educational_value,
                feedback="Automated evaluation - manual review recommended",
                is_approved=overall_score >= 7.0,
                improvements=["Review question structure", "Verify against source material"]
            )
            results.append(result)
        
        return results
    
    def filter_approved_questions(
        self,
        questions: List[QuestionData],
        evaluations: List[EvaluationResult]
    ) -> List[QuestionData]:
        """Filter questions that meet quality standards."""
        approved_questions = []
        
        for question, evaluation in zip(questions, evaluations):
            if evaluation.is_approved:
                approved_questions.append(question)
        
        return approved_questions
    
    def get_evaluation_summary(self, evaluations: List[EvaluationResult]) -> Dict[str, Any]:
        """Get summary statistics for evaluations."""
        if not evaluations:
            return {"total": 0, "approved": 0, "average_score": 0.0}
        
        total = len(evaluations)
        approved = sum(1 for e in evaluations if e.is_approved)
        average_score = sum(e.overall_score for e in evaluations) / total
        
        return {
            "total": total,
            "approved": approved,
            "approval_rate": approved / total,
            "average_score": round(average_score, 2),
            "score_breakdown": {
                "clarity": round(sum(e.clarity_score for e in evaluations) / total, 2),
                "difficulty": round(sum(e.difficulty_appropriateness for e in evaluations) / total, 2),
                "accuracy": round(sum(e.content_accuracy for e in evaluations) / total, 2),
                "educational_value": round(sum(e.educational_value for e in evaluations) / total, 2)
            }
        } 