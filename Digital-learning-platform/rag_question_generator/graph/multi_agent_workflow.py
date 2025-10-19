"""Multi-agent workflow for orchestrating question generation and evaluation."""

from typing import List, Dict, Any, Optional, TypedDict
from langchain_core.documents import Document
from langgraph.graph import StateGraph, END
from ..agents.question_generator import QuestionGeneratorAgent, QuestionData
from ..agents.question_evaluator import QuestionEvaluatorAgent, EvaluationResult
from ..agents.question_optimizer import QuestionOptimizerAgent
from ..utils.vector_store import VectorStore


class WorkflowState(TypedDict):
    """State for the multi-agent workflow."""
    concept: str
    query: str
    retrieved_documents: List[Document]
    context: str
    generated_questions: List[QuestionData]
    evaluations: List[EvaluationResult]
    approved_questions: List[QuestionData]
    evaluation_summary: Dict[str, Any]
    question_types: List[str]
    num_questions: int
    error: Optional[str]
    status: str
    current_iteration: int
    max_iterations: int
    optimization_feedback: str


class MultiAgentWorkflow:
    """Orchestrates the multi-agent question generation and evaluation workflow."""
    
    def __init__(
        self,
        vector_store: VectorStore,
        question_generator: Optional[QuestionGeneratorAgent] = None,
        question_evaluator: Optional[QuestionEvaluatorAgent] = None,
        question_optimizer: Optional[QuestionOptimizerAgent] = None
    ):
        self.vector_store = vector_store
        self.question_generator = question_generator or QuestionGeneratorAgent()
        self.question_evaluator = question_evaluator or QuestionEvaluatorAgent()
        self.question_optimizer = question_optimizer or QuestionOptimizerAgent()
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self):
        """Build the LangGraph workflow with iterative optimization."""
        
        # Create the state graph
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("retrieve", self._retrieve_documents)
        workflow.add_node("generate", self._generate_questions)
        workflow.add_node("evaluate", self._evaluate_questions)
        workflow.add_node("optimize", self._optimize_questions)
        workflow.add_node("finalize", self._finalize_results)
        
        # Add edges
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", "evaluate")
        
        # Conditional edge: if approved or max iterations reached -> finalize, else -> optimize
        workflow.add_conditional_edges(
            "evaluate",
            self._should_optimize,
            {
                "optimize": "optimize",
                "finalize": "finalize"
            }
        )
        
        # After optimization, loop back to evaluate
        workflow.add_edge("optimize", "evaluate")
        workflow.add_edge("finalize", END)
        
        # Compile the graph
        return workflow.compile()
    
    def _retrieve_documents(self, state: WorkflowState) -> WorkflowState:
        """Retrieve relevant documents from vector store."""
        try:
            concept = state["concept"]
            query = state.get("query", concept)
            
            print(f"\n🔍 DEBUG: Searching for concept: '{concept}'")
            print(f"🔍 DEBUG: Using query: '{query}'")
            
            # Perform similarity search
            documents = self.vector_store.similarity_search(
                query=query,
                k=5  # Retrieve top 5 most relevant documents
            )
            
            print(f"📄 DEBUG: Found {len(documents)} relevant document chunks")
            
            # Show retrieved content for debugging
            for i, doc in enumerate(documents, 1):
                print(f"\n--- CHUNK {i} (from {doc.metadata.get('filename', 'unknown')}) ---")
                print(f"Content preview: {doc.page_content[:200]}...")
                print(f"Full length: {len(doc.page_content)} characters")
            
            # Prepare context from documents
            context = "\n\n".join([doc.page_content for doc in documents])
            
            print(f"\n📝 DEBUG: Total context length: {len(context)} characters")
            print(f"📝 DEBUG: Context preview (first 300 chars):")
            print("-" * 50)
            print(context[:300] + "..." if len(context) > 300 else context)
            print("-" * 50)
            
            state.update({
                "retrieved_documents": documents,
                "context": context,
                "status": "documents_retrieved"
            })
            
        except Exception as e:
            state.update({
                "error": f"Document retrieval failed: {str(e)}",
                "status": "retrieval_failed"
            })
        
        return state
    
    def _generate_questions(self, state: WorkflowState) -> WorkflowState:
        """Generate questions using the question generator agent."""
        try:
            if state.get("error"):
                return state
            
            concept = state["concept"]
            documents = state["retrieved_documents"]
            question_types = state.get("question_types", ["mcq", "fill_blank"])
            num_questions = state.get("num_questions", 5)
            
            print(f"\n🎯 DEBUG: Generating questions for concept: '{concept}'")
            print(f"🎯 DEBUG: Question types: {question_types}")
            print(f"🎯 DEBUG: Number of questions: {num_questions}")
            print(f"🎯 DEBUG: Using {len(documents)} document chunks")
            
            # Generate questions
            questions = self.question_generator.generate_from_documents(
                documents=documents,
                concept=concept,
                question_types=question_types,
                num_questions=num_questions
            )
            
            print(f"\n✅ DEBUG: Generated {len(questions)} questions")
            for i, q in enumerate(questions, 1):
                print(f"   Question {i}: {q.question_type.upper()} - {q.question[:100]}...")
            
            state.update({
                "generated_questions": questions,
                "status": "questions_generated"
            })
            
        except Exception as e:
            state.update({
                "error": f"Question generation failed: {str(e)}",
                "status": "generation_failed"
            })
        
        return state
    
    def _evaluate_questions(self, state: WorkflowState) -> WorkflowState:
        """Evaluate questions using the question evaluator agent."""
        try:
            if state.get("error"):
                return state
            
            questions = state["generated_questions"]
            context = state["context"]
            current_iteration = state.get("current_iteration", 1)
            
            if not questions:
                state.update({
                    "error": "No questions to evaluate",
                    "status": "evaluation_failed"
                })
                return state
            
            print(f"\n📊 DEBUG: Evaluating questions (Iteration {current_iteration}/{state.get('max_iterations', 5)})")
            
            # Evaluate questions
            evaluations = self.question_evaluator.evaluate_questions(
                questions=questions,
                source_context=context
            )
            
            # Filter approved questions
            approved_questions = self.question_evaluator.filter_approved_questions(
                questions=questions,
                evaluations=evaluations
            )
            
            # Get evaluation summary
            evaluation_summary = self.question_evaluator.get_evaluation_summary(evaluations)
            
            # Prepare optimization feedback for unapproved questions
            optimization_feedback = self._prepare_optimization_feedback(evaluations)
            
            print(f"✅ DEBUG: {len(approved_questions)}/{len(questions)} questions approved")
            print(f"📈 DEBUG: Average score: {evaluation_summary.get('average_score', 0)}")
            
            state.update({
                "evaluations": evaluations,
                "approved_questions": approved_questions,
                "evaluation_summary": evaluation_summary,
                "optimization_feedback": optimization_feedback,
                "status": "questions_evaluated"
            })
            
        except Exception as e:
            state.update({
                "error": f"Question evaluation failed: {str(e)}",
                "status": "evaluation_failed"
            })
        
        return state
    
    def _should_optimize(self, state: WorkflowState) -> str:
        """Determine whether to optimize or finalize based on evaluation results."""
        
        # Check if there's an error
        if state.get("error"):
            return "finalize"
        
        # Get current iteration and max iterations
        current_iteration = state.get("current_iteration", 1)
        max_iterations = state.get("max_iterations", 5)
        
        # Check if we've reached max iterations
        if current_iteration >= max_iterations:
            print(f"\n⚠️ DEBUG: Max iterations ({max_iterations}) reached. Finalizing...")
            return "finalize"
        
        # Check if all questions are approved
        approved_questions = state.get("approved_questions", [])
        total_questions = len(state.get("generated_questions", []))
        
        if len(approved_questions) == total_questions and total_questions > 0:
            print(f"\n✅ DEBUG: All {total_questions} questions approved! Finalizing...")
            return "finalize"
        
        # Otherwise, optimize
        print(f"\n🔧 DEBUG: {len(approved_questions)}/{total_questions} approved. Optimizing...")
        return "optimize"
    
    def _optimize_questions(self, state: WorkflowState) -> WorkflowState:
        """Optimize questions based on evaluation feedback."""
        try:
            if state.get("error"):
                return state
            
            questions = state["generated_questions"]
            evaluations = state["evaluations"]
            context = state["context"]
            current_iteration = state.get("current_iteration", 1)
            
            print(f"\n🔧 DEBUG: Optimizing questions (Iteration {current_iteration})")
            
            # Optimize questions
            optimized_questions = self.question_optimizer.optimize_questions(
                questions=questions,
                evaluations=evaluations,
                source_context=context
            )
            
            # Increment iteration counter
            new_iteration = current_iteration + 1
            
            print(f"✅ DEBUG: Questions optimized. Moving to iteration {new_iteration}")
            
            state.update({
                "generated_questions": optimized_questions,
                "current_iteration": new_iteration,
                "status": "questions_optimized"
            })
            
        except Exception as e:
            state.update({
                "error": f"Question optimization failed: {str(e)}",
                "status": "optimization_failed"
            })
        
        return state
    
    def _prepare_optimization_feedback(self, evaluations: List[EvaluationResult]) -> str:
        """Prepare feedback summary for optimization."""
        feedback_parts = []
        
        for i, eval_result in enumerate(evaluations, 1):
            if not eval_result.is_approved:
                feedback_parts.append(
                    f"Q{i}: Score {eval_result.overall_score}/10. "
                    f"Issues: {eval_result.feedback}. "
                    f"Improvements: {', '.join(eval_result.improvements)}"
                )
        
        return "\n".join(feedback_parts) if feedback_parts else "All questions approved"
    
    def _finalize_results(self, state: WorkflowState) -> WorkflowState:
        """Finalize the workflow results."""
        try:
            if state.get("error"):
                state.update({"status": "workflow_failed"})
                return state
            
            # Check if we have approved questions
            approved_questions = state.get("approved_questions", [])
            
            if not approved_questions:
                state.update({
                    "error": "No questions met quality standards",
                    "status": "no_approved_questions"
                })
            else:
                state.update({"status": "workflow_completed"})
            
        except Exception as e:
            state.update({
                "error": f"Workflow finalization failed: {str(e)}",
                "status": "finalization_failed"
            })
        
        return state
    
    def run_workflow(
        self,
        concept: str,
        query: Optional[str] = None,
        question_types: List[str] = ["mcq", "fill_blank"],
        num_questions: int = 5,
        max_iterations: int = 5
    ) -> WorkflowState:
        """Run the complete multi-agent workflow with iterative optimization."""
        
        # Initialize state
        initial_state: WorkflowState = {
            "concept": concept,
            "query": query or concept,
            "retrieved_documents": [],
            "context": "",
            "generated_questions": [],
            "evaluations": [],
            "approved_questions": [],
            "evaluation_summary": {},
            "question_types": question_types,
            "num_questions": num_questions,
            "error": None,
            "status": "initialized",
            "current_iteration": 1,
            "max_iterations": max_iterations,
            "optimization_feedback": ""
        }
        
        # Run the workflow
        try:
            result = self.workflow.invoke(initial_state)
            return result
        except Exception as e:
            initial_state.update({
                "error": f"Workflow execution failed: {str(e)}",
                "status": "execution_failed"
            })
            return initial_state
    
    def get_workflow_status(self, state: WorkflowState) -> Dict[str, Any]:
        """Get a summary of the workflow status."""
        return {
            "status": state.get("status", "unknown"),
            "error": state.get("error"),
            "documents_retrieved": len(state.get("retrieved_documents", [])),
            "questions_generated": len(state.get("generated_questions", [])),
            "questions_approved": len(state.get("approved_questions", [])),
            "evaluation_summary": state.get("evaluation_summary", {}),
            "current_iteration": state.get("current_iteration", 1),
            "max_iterations": state.get("max_iterations", 5),
            "optimization_feedback": state.get("optimization_feedback", "")
        } 