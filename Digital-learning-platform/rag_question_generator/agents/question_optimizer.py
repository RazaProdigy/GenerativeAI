"""Question optimizer agent for improving questions based on evaluation feedback."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.language_models.llms import LLM
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from .question_generator import QuestionData
from .question_evaluator import EvaluationResult
import json


class QuestionOptimizerAgent:
    """Agent responsible for optimizing questions based on evaluation feedback."""
    
    def __init__(self, llm: Optional[LLM] = None, temperature: float = 0.7):
        self.llm = llm or ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=temperature
        )
        
        self.optimization_prompt = PromptTemplate(
            input_variables=["questions", "evaluations", "source_context"],
            template="""
You are an expert educational content optimizer. Your task is to improve questions based on evaluation feedback.

Source Context:
{source_context}

Original Questions with Evaluation Feedback:
{questions_with_feedback}

Your task:
1. Review each question that was NOT approved (is_approved: false)
2. Address the specific issues mentioned in the feedback and improvements
3. Optimize the questions to meet quality standards:
   - Minimum overall score of 7.0
   - All individual scores should be >= 6.0
   - Clear, unambiguous language
   - Factually accurate
   - Educationally valuable
   - Well-constructed options (for MCQ)

For APPROVED questions (is_approved: true), keep them EXACTLY as they are - do not modify them.

Return ALL questions (both approved and optimized ones) in the SAME ORDER as provided, in JSON format:

[
    {{
        "question": "Improved or original question text",
        "question_type": "mcq|fill_blank",
        "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
        "correct_answer": "Correct answer",
        "explanation": "Enhanced explanation",
        "difficulty": "easy|medium|hard",
        "topic": "Topic covered"
    }}
]

IMPORTANT: 
- Return ALL questions in the same order
- Keep approved questions unchanged
- Only optimize questions that were not approved
- Ensure JSON format is valid

Optimize the questions:
"""
        )
        
        self.optimization_chain = self.optimization_prompt | self.llm
    
    def optimize_questions(
        self,
        questions: List[QuestionData],
        evaluations: List[EvaluationResult],
        source_context: str
    ) -> List[QuestionData]:
        """Optimize questions based on evaluation feedback."""
        
        if not questions or not evaluations:
            return questions
        
        # Prepare questions with feedback
        questions_with_feedback = self._format_questions_with_feedback(questions, evaluations)
        
        try:
            # Get optimized questions from LLM
            response = self.optimization_chain.invoke({
                "questions_with_feedback": questions_with_feedback,
                "source_context": source_context[:3000]  # Limit context to avoid token limits
            })
            
            # Parse optimization results
            response_content = response.content if hasattr(response, 'content') else str(response)
            optimized_data = self._parse_json_response(response_content)
            
            # Create QuestionData objects
            optimized_questions = []
            for i, q_data in enumerate(optimized_data):
                try:
                    question = QuestionData(**q_data)
                    optimized_questions.append(question)
                except Exception as e:
                    print(f"Error creating optimized question {i}: {e}")
                    # Fall back to original question if optimization failed
                    if i < len(questions):
                        optimized_questions.append(questions[i])
            
            # If we got fewer questions than expected, fill with originals
            while len(optimized_questions) < len(questions):
                optimized_questions.append(questions[len(optimized_questions)])
            
            print(f"\n🔧 DEBUG: Optimized {len(optimized_questions)} questions")
            
            return optimized_questions
            
        except Exception as e:
            print(f"Error during optimization: {e}")
            # Return original questions if optimization fails
            return questions
    
    def _format_questions_with_feedback(
        self,
        questions: List[QuestionData],
        evaluations: List[EvaluationResult]
    ) -> str:
        """Format questions with their evaluation feedback."""
        formatted = []
        
        for i, (q, eval_result) in enumerate(zip(questions, evaluations), 1):
            question_text = f"Question {i}:\n"
            question_text += f"Type: {q.question_type}\n"
            question_text += f"Question: {q.question}\n"
            
            if q.options:
                question_text += f"Options: {', '.join(q.options)}\n"
            
            question_text += f"Correct Answer: {q.correct_answer}\n"
            question_text += f"Explanation: {q.explanation}\n"
            question_text += f"Difficulty: {q.difficulty}\n"
            question_text += f"Topic: {q.topic}\n\n"
            
            # Add evaluation feedback
            question_text += f"Evaluation:\n"
            question_text += f"- Approved: {eval_result.is_approved}\n"
            question_text += f"- Overall Score: {eval_result.overall_score}/10\n"
            question_text += f"- Clarity Score: {eval_result.clarity_score}/10\n"
            question_text += f"- Difficulty Appropriateness: {eval_result.difficulty_appropriateness}/10\n"
            question_text += f"- Content Accuracy: {eval_result.content_accuracy}/10\n"
            question_text += f"- Educational Value: {eval_result.educational_value}/10\n"
            question_text += f"- Feedback: {eval_result.feedback}\n"
            
            if eval_result.improvements:
                question_text += f"- Improvements Needed: {', '.join(eval_result.improvements)}\n"
            
            formatted.append(question_text)
        
        return "\n\n".join(formatted)
    
    def _parse_json_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse JSON response from LLM."""
        try:
            # Clean the response
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            
            # Parse JSON
            questions_data = json.loads(cleaned_response.strip())
            
            if not isinstance(questions_data, list):
                questions_data = [questions_data]
            
            return questions_data
            
        except json.JSONDecodeError as e:
            print(f"Error parsing optimization response: {e}")
            print(f"Response: {response}")
            return []

