"""Simple test script for the RAG Question Generator API."""

import asyncio
import httpx
import json
from pathlib import Path


async def test_api():
    """Test the basic API functionality."""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # Test health endpoint
        print("Testing health endpoint...")
        health_response = await client.get(f"{base_url}/health")
        print(f"Health status: {health_response.status_code}")
        print(f"Response: {health_response.json()}")
        
        # Test root endpoint
        print("\nTesting root endpoint...")
        root_response = await client.get(f"{base_url}/")
        print(f"Root status: {root_response.status_code}")
        print(f"Response: {root_response.json()}")
        
        # Test question generation (will fail without PDF upload)
        print("\nTesting question generation endpoint...")
        question_request = {
            "concept": "machine learning",
            "question_types": ["mcq", "fill_blank"],
            "num_questions": 3
        }
        
        questions_response = await client.post(
            f"{base_url}/generate/questions",
            json=question_request
        )
        print(f"Questions status: {questions_response.status_code}")
        
        if questions_response.status_code == 400:
            print("Expected error (no PDF uploaded):", questions_response.json())
        else:
            print(f"Response: {questions_response.json()}")


async def test_with_sample_pdf():
    """Test with a sample PDF if available."""
    base_url = "http://localhost:8000"
    
    # You can place a sample PDF in the same directory as this script
    sample_pdf_path = Path("sample.pdf")
    
    if not sample_pdf_path.exists():
        print(f"Sample PDF not found at {sample_pdf_path}. Skipping PDF test.")
        return
    
    async with httpx.AsyncClient() as client:
        # Upload PDF
        print("Testing PDF upload...")
        with open(sample_pdf_path, "rb") as pdf_file:
            files = {"file": ("sample.pdf", pdf_file, "application/pdf")}
            ingest_response = await client.post(f"{base_url}/ingest", files=files)
        
        print(f"Ingest status: {ingest_response.status_code}")
        if ingest_response.status_code == 200:
            ingest_data = ingest_response.json()
            print(f"Document processed successfully!")
            print(f"TOC items: {len(ingest_data['table_of_contents'])}")
            print(f"Text chunks: {ingest_data['document_stats']['num_chunks']}")
            
            # Now test question generation
            print("\nTesting question generation with PDF...")
            question_request = {
                "concept": "key concepts from the document",
                "question_types": ["mcq"],
                "num_questions": 2
            }
            
            questions_response = await client.post(
                f"{base_url}/generate/questions",
                json=question_request
            )
            print(f"Questions status: {questions_response.status_code}")
            
            if questions_response.status_code == 200:
                questions_data = questions_response.json()
                print(f"Generated {len(questions_data['questions'])} questions")
                print(f"Approved {len(questions_data['approved_questions'])} questions")
            else:
                print(f"Error: {questions_response.json()}")
        else:
            print(f"Error uploading PDF: {ingest_response.json()}")


if __name__ == "__main__":
    print("Testing RAG Question Generator API...")
    print("=" * 50)
    
    asyncio.run(test_api())
    
    print("\n" + "=" * 50)
    print("Testing with sample PDF (if available)...")
    
    asyncio.run(test_with_sample_pdf())
    
    print("\nTesting complete!") 