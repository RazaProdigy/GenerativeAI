"""Quick test script for your PDF."""

import requests
import json
import sys
from pathlib import Path

def test_with_your_pdf(pdf_path, concept="key concepts"):
    """Test the system with your specific PDF."""
    
    base_url = "http://localhost:8000"
    
    # Check if PDF exists
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"❌ PDF file not found: {pdf_path}")
        print("Please provide the correct path to your PDF file.")
        return
    
    print(f"🔍 Testing with PDF: {pdf_file.name}")
    print(f"📖 Concept: {concept}")
    print("=" * 50)
    
    try:
        # 1. Health check
        print("1. Checking API health...")
        health_response = requests.get(f"{base_url}/health")
        if health_response.status_code == 200:
            print("✅ API is healthy")
        else:
            print("❌ API health check failed")
            return
        
        # 2. Upload PDF
        print("2. Uploading PDF...")
        with open(pdf_file, "rb") as f:
            files = {"file": (pdf_file.name, f, "application/pdf")}
            upload_response = requests.post(f"{base_url}/ingest", files=files)
        
        if upload_response.status_code == 200:
            upload_data = upload_response.json()
            print("✅ PDF uploaded successfully!")
            print(f"   📄 Filename: {upload_data['document_stats']['filename']}")
            print(f"   📊 Text length: {upload_data['document_stats']['text_length']:,} characters")
            print(f"   🧩 Number of chunks: {upload_data['document_stats']['num_chunks']}")
            print(f"   📑 Table of contents items: {len(upload_data['table_of_contents'])}")
        else:
            print(f"❌ PDF upload failed: {upload_response.text}")
            return
        
        # 3. Generate questions
        print("3. Generating questions...")
        question_request = {
            "concept": concept,
            "question_types": ["mcq", "fill_blank"],
            "num_questions": 3
        }
        
        questions_response = requests.post(
            f"{base_url}/generate/questions",
            json=question_request
        )
        
        if questions_response.status_code == 200:
            questions_data = questions_response.json()
            print("✅ Questions generated successfully!")
            
            # Display results
            print(f"\n📋 Generated {len(questions_data['questions'])} questions")
            print(f"✅ Approved {len(questions_data['approved_questions'])} questions")
            print(f"📊 Average quality score: {questions_data['evaluation_summary'].get('average_score', 'N/A')}")
            
            # Show first approved question as example
            if questions_data['approved_questions']:
                print(f"\n🎯 Example Question:")
                q = questions_data['approved_questions'][0]
                print(f"   Type: {q['question_type'].upper()}")
                print(f"   Question: {q['question']}")
                if q['options']:
                    for option in q['options']:
                        print(f"   {option}")
                print(f"   ✅ Correct Answer: {q['correct_answer']}")
                print(f"   📚 Explanation: {q['explanation']}")
                print(f"   📈 Difficulty: {q['difficulty']}")
            
            print(f"\n💾 Full response saved to 'questions_output.json'")
            with open("questions_output.json", "w") as f:
                json.dump(questions_data, f, indent=2)
                
        else:
            print(f"❌ Question generation failed: {questions_response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure the server is running:")
        print("   python run.py")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        concept = sys.argv[2] if len(sys.argv) > 2 else "key concepts"
        test_with_your_pdf(pdf_path, concept)
    else:
        print("Usage: python quick_test.py <path_to_your_pdf> [concept]")
        print("Example: python quick_test.py my_document.pdf 'machine learning'")