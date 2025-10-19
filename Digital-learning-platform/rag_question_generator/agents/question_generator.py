"""Question generator agent for creating MCQ and fill-in-the-blank questions."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.documents import Document
from langchain_core.language_models.llms import LLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
import json


class QuestionData(BaseModel):
    """Data model for a generated question."""
    question: str = Field(description="The question text")
    question_type: str = Field(description="Type of question: 'mcq' or 'fill_blank'")
    options: Optional[List[str]] = Field(default=None, description="Options for MCQ questions")
    correct_answer: str = Field(description="The correct answer")
    explanation: str = Field(description="Explanation for the answer")
    difficulty: str = Field(description="Difficulty level: easy, medium, hard")
    topic: str = Field(description="Main topic/concept covered")


class QuestionGeneratorAgent:
    """Agent responsible for generating questions from retrieved content."""
    
    def __init__(self, llm: Optional[LLM] = None, temperature: float = 0.7):
        self.llm = llm or ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=temperature
        )
        
        self.mcq_prompt = PromptTemplate(
            input_variables=["context", "concept", "num_questions"],
            template="""
You are an expert educational content creator. Based on the provided context, generate {num_questions} multiple choice questions (MCQ) about the concept: "{concept}".

Context:
{context}

Requirements:
1. Create clear, unambiguous questions
2. Provide 4 options (A, B, C, D) for each question
3. Ensure only one correct answer per question
4. Include questions of varying difficulty (easy, medium, hard)
5. Focus on understanding, application, and analysis rather than just recall
6. Make distractors plausible but clearly incorrect

Return the response as a JSON array with the following structure for each question:
{{
    "question": "Question text here?",
    "question_type": "mcq",
    "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
    "correct_answer": "A) Option 1",
    "explanation": "Detailed explanation of why this is correct and others are wrong",
    "difficulty": "easy|medium|hard",
    "topic": "Specific topic/concept"
}}

Generate exactly {num_questions} questions:
"""
        )
        
        self.fill_blank_prompt = PromptTemplate(
            input_variables=["context", "concept", "num_questions"],
            template="""
You are an expert educational content creator. Based on the provided context, generate {num_questions} fill-in-the-blank questions about the concept: "{concept}".

Context:
{context}

Requirements:
1. Create sentences with strategic blanks that test key concepts
2. Blanks should be for important terms, concepts, or values
3. Provide clear context so the answer is determinable
4. Include questions of varying difficulty (easy, medium, hard)
5. Focus on key terminology and important relationships

Return the response as a JSON array with the following structure for each question:
{{
    "question": "This is a sentence with a _______ that needs to be filled.",
    "question_type": "fill_blank",
    "options": null,
    "correct_answer": "correct term or phrase",
    "explanation": "Explanation of the concept and why this answer fits",
    "difficulty": "easy|medium|hard",
    "topic": "Specific topic/concept"
}}

Generate exactly {num_questions} questions:
"""
        )
        
        # Create runnable chains using the new pattern
        self.mcq_chain = self.mcq_prompt | self.llm
        self.fill_blank_chain = self.fill_blank_prompt | self.llm
    
    def generate_questions(
        self,
        context: str,
        concept: str,
        question_types: List[str] = ["mcq", "fill_blank"],
        num_questions: int = 5
    ) -> List[QuestionData]:
        """Generate questions based on context and concept."""
        
        all_questions = []
        
        for question_type in question_types:
            if question_type == "mcq":
                questions = self._generate_mcq_questions(context, concept, num_questions // len(question_types))
            elif question_type == "fill_blank":
                questions = self._generate_fill_blank_questions(context, concept, num_questions // len(question_types))
            else:
                continue
            
            all_questions.extend(questions)
        
        return all_questions
    
    def _generate_mcq_questions(self, context: str, concept: str, num_questions: int) -> List[QuestionData]:
        """Generate MCQ questions."""
        try:
            response = self.mcq_chain.invoke({
                "context": context,
                "concept": concept,
                "num_questions": num_questions
            })
            
            # Parse JSON response (extract content from message object)
            response_content = response.content if hasattr(response, 'content') else str(response)
            questions_data = self._parse_json_response(response_content)
            return [QuestionData(**q) for q in questions_data]
            
        except Exception as e:
            print(f"Error generating MCQ questions: {e}")
            return []
    
    def _generate_fill_blank_questions(self, context: str, concept: str, num_questions: int) -> List[QuestionData]:
        """Generate fill-in-the-blank questions."""
        try:
            response = self.fill_blank_chain.invoke({
                "context": context,
                "concept": concept,
                "num_questions": num_questions
            })
            
            # Parse JSON response (extract content from message object)
            response_content = response.content if hasattr(response, 'content') else str(response)
            questions_data = self._parse_json_response(response_content)
            return [QuestionData(**q) for q in questions_data]
            
        except Exception as e:
            print(f"Error generating fill-in-the-blank questions: {e}")
            return []
    
    def _parse_json_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse JSON response from LLM."""
        try:
            # Clean the response - remove any markdown formatting
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
            print(f"Error parsing JSON response: {e}")
            print(f"Response: {response}")
            return []
    
    def generate_from_documents(
        self,
        documents: List[Document],
        concept: str,
        question_types: List[str] = ["mcq", "fill_blank"],
        num_questions: int = 5
    ) -> List[QuestionData]:
        """Generate questions from retrieved documents."""
        
        print(f"\n🤖 DEBUG: Question Generator received {len(documents)} documents")
        
        # Combine document content
        context = "\n\n".join([doc.page_content for doc in documents])
        
        print(f"🤖 DEBUG: Combined context length: {len(context)} characters")
        
        # Limit context length to avoid token limits
        max_context_length = 4000
        if len(context) > max_context_length:
            print(f"🤖 DEBUG: Context too long, truncating to {max_context_length} characters")
            context = context[:max_context_length] + "..."
        
        print(f"🤖 DEBUG: Final context being sent to LLM:")
        print("=" * 60)
        print(context[:500] + "..." if len(context) > 500 else context)
        print("=" * 60)
        
        return self.generate_questions(context, concept, question_types, num_questions) 