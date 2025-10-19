"""Quick test to verify setup is working correctly."""

def test_basic_imports():
    """Test basic imports and system readiness."""
    print("🔍 Testing RAG Question Generator Setup...")
    print("=" * 50)
    
    try:
        # Test core dependencies
        import fastapi
        print("✅ FastAPI: OK")
        
        import uvicorn
        print("✅ Uvicorn: OK")
        
        import PyPDF2
        print("✅ PyPDF2: OK")
        
        import chromadb
        print("✅ ChromaDB: OK")
        
        import langchain
        print("✅ LangChain: OK")
        
        # Test our modules
        from rag_question_generator.utils.pdf_processor import PDFProcessor
        print("✅ PDF Processor: OK")
        
        from rag_question_generator.utils.vector_store import VectorStore
        print("✅ Vector Store: OK")
        
        from rag_question_generator.agents.question_generator import QuestionGeneratorAgent
        print("✅ Question Generator Agent: OK")
        
        from rag_question_generator.agents.question_evaluator import QuestionEvaluatorAgent
        print("✅ Question Evaluator Agent: OK")
        
        from rag_question_generator.graph.multi_agent_workflow import MultiAgentWorkflow
        print("✅ Multi-Agent Workflow: OK")
        
        from rag_question_generator.api.endpoints import app
        print("✅ API Endpoints: OK")
        
        print("\n🎉 Setup verification complete! System is ready to use.")
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("\n💡 Run: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_basic_imports()