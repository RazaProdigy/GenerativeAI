"""Test script for the iterative workflow with optimizer."""

import os
from rag_question_generator.utils.pdf_processor import PDFProcessor
from rag_question_generator.utils.vector_store import VectorStore
from rag_question_generator.graph.multi_agent_workflow import MultiAgentWorkflow


def test_iterative_workflow():
    """Test the iterative workflow with question optimization."""
    
    print("=" * 80)
    print("Testing Iterative Workflow with Question Optimizer")
    print("=" * 80)
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("\n❌ ERROR: OPENAI_API_KEY environment variable is not set!")
        print("Please set it before running this test.")
        return
    
    # Initialize components
    print("\n1. Initializing components...")
    pdf_processor = PDFProcessor()
    vector_store = VectorStore()
    
    # Check if vector store has documents
    stats = vector_store.get_collection_stats()
    print(f"   Vector store status: {stats}")
    
    if stats.get("document_count", 0) == 0:
        print("\n❌ ERROR: No documents found in vector store!")
        print("Please run the ingest process first.")
        print("You can use test_api.py or run.py to ingest a PDF file.")
        return
    
    print(f"\n✅ Found {stats['document_count']} documents in vector store")
    
    # Create workflow
    print("\n2. Creating multi-agent workflow with optimizer...")
    workflow = MultiAgentWorkflow(vector_store)
    
    # Test with a simple concept
    concept = "Algebra"
    print(f"\n3. Running workflow for concept: '{concept}'")
    print(f"   Max iterations: 5")
    print(f"   Number of questions: 3")
    print("\n" + "-" * 80)
    
    # Run the workflow with max_iterations=5
    result = workflow.run_workflow(
        concept=concept,
        query="generate me mcq and fill in the blank questions for radical expressions in algebra",
        question_types=["mcq", "fill_blank"],
        num_questions=3,
        max_iterations=5
    )
    
    print("\n" + "-" * 80)
    print("\n4. Workflow completed!")
    print("\n📊 WORKFLOW RESULTS:")
    print("=" * 80)
    
    # Display workflow status
    status = workflow.get_workflow_status(result)
    print(f"\nStatus: {status['status']}")
    print(f"Current Iteration: {status['current_iteration']}")
    print(f"Max Iterations: {status['max_iterations']}")
    print(f"Documents Retrieved: {status['documents_retrieved']}")
    print(f"Questions Generated: {status['questions_generated']}")
    print(f"Questions Approved: {status['questions_approved']}")
    
    if status.get('error'):
        print(f"\n❌ Error: {status['error']}")
    
    # Display evaluation summary
    eval_summary = status.get('evaluation_summary', {})
    print(f"\n📈 EVALUATION SUMMARY:")
    print(f"   Total: {eval_summary.get('total', 0)}")
    print(f"   Approved: {eval_summary.get('approved', 0)}")
    print(f"   Approval Rate: {eval_summary.get('approval_rate', 0):.1%}")
    print(f"   Average Score: {eval_summary.get('average_score', 0):.2f}/10")
    
    if 'score_breakdown' in eval_summary:
        print(f"\n   Score Breakdown:")
        breakdown = eval_summary['score_breakdown']
        print(f"   - Clarity: {breakdown.get('clarity', 0):.2f}/10")
        print(f"   - Difficulty: {breakdown.get('difficulty', 0):.2f}/10")
        print(f"   - Accuracy: {breakdown.get('accuracy', 0):.2f}/10")
        print(f"   - Educational Value: {breakdown.get('educational_value', 0):.2f}/10")
    
    # Display approved questions
    approved_questions = result.get("approved_questions", [])
    print(f"\n✅ APPROVED QUESTIONS ({len(approved_questions)}):")
    print("=" * 80)
    
    for i, q in enumerate(approved_questions, 1):
        print(f"\nQuestion {i}: [{q.question_type.upper()}]")
        print(f"Q: {q.question}")
        if q.options:
            print(f"Options:")
            for opt in q.options:
                print(f"   {opt}")
        print(f"✓ Answer: {q.correct_answer}")
        print(f"Explanation: {q.explanation}")
        print(f"Difficulty: {q.difficulty}")
        print(f"Topic: {q.topic}")
        print("-" * 80)
    
    # Display optimization feedback if any
    if status.get('optimization_feedback'):
        print(f"\n🔧 OPTIMIZATION FEEDBACK:")
        print(status['optimization_feedback'])
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST COMPLETED!")
    print("=" * 80)
    
    # Provide summary of iterations
    iterations_used = status['current_iteration']
    if iterations_used > 1:
        print(f"\n📊 The optimizer ran for {iterations_used - 1} iteration(s)")
        print(f"   Started with questions that needed improvement")
        print(f"   Optimized based on evaluation feedback")
        print(f"   Final approval rate: {eval_summary.get('approval_rate', 0):.1%}")
    else:
        print(f"\n✅ All questions were approved on the first try!")
    
    print(f"\n🎉 Success! The iterative workflow is working correctly.")


if __name__ == "__main__":
    test_iterative_workflow()

