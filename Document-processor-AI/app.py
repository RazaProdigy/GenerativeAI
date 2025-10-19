# fast api pipeline
# post /ask {"question": "What is the capital of France?"}
# get /metrics {Prometheus scrape will be done here}

import time, uuid, logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from cache_store import get as cache_get, set as cache_set
from llm_client import call as llm_call
from postprocess import secure_output
from guardrails import apply_guardrails
from observability import log as audit_log, record_metric, start_metrics_server
from config import CACHE_TTL_SECONDS, CACHE_SIMILARITY_THRESHOLD
from retrieval import retrieve_context
from router import build_prompt
import uvicorn
app = FastAPI(
    title="GenAI RAG Pipeline",
    description="A pipeline for answering questions using GenAI and RAG with guardrails, caching and metrics",
    version="1.0.0"
)
start_metrics_server(port = 8002)

# pydantic schema for the request body
class AskRequest(BaseModel):
    question: str
    user_id: str | None = None

class AskResponse(BaseModel):
    answer: str
    user_id: str | None = None

def run_pipeline(question: str, user_id: str | None = None)-> str:
    """
    Run the pipeline for a given question and user id
    """
    # step 1 : Check cache with semantic similarity
    cached = cache_get(question, similarity_threshold=CACHE_SIMILARITY_THRESHOLD)
    if cached:
        logging.info(f"Semantic cache hit for question: {question}")
        return AskResponse(answer=cached, user_id=user_id)
    
    # step 2 : Retrive context
    t0 = time.time()
    context = retrieve_context(question)
    retrieval_latency = int( (time.time() - t0)*1000) # in milliseconds
    record_metric("retrieval_latency_ms", retrieval_latency)
    logging.info(f"Retrieval latency: {retrieval_latency}ms")
    logging.info("Retrieved context:")
    logging.info(context)
    record_metric("retrieval_latency_ms", retrieval_latency)

    # prompt    
    model, prompt = build_prompt(question, context)

    t1 = time.time()
    raw_answer = llm_call(model, prompt)
    llm_latency = int( (time.time() - t1)*1000) # in milliseconds
    record_metric("llm_latency_ms", llm_latency)
    logging.info(f"LLM latency: {llm_latency}ms")
    logging.info("Raw answer:")
    logging.info(raw_answer)
    record_metric("llm_latency_ms", llm_latency)
    
    # Post processing
    post_processed = secure_output(raw_answer)
    logging.info("Post processed answer:")
    logging.info(post_processed)
    record_metric("llm_latency_ms", llm_latency)
    
    # Apply guardrails
    secured = apply_guardrails(post_processed)
    logging.info("Secured answer:")
    logging.info(secured)

    # Audit log
    audit_log(question, prompt, post_processed, secured, model=model, latency_ms=retrieval_latency + llm_latency, retrieved_context=context,user_id=user_id)

    # Cache the answer
    cache_set(question, secured, CACHE_TTL_SECONDS)

    return AskResponse(answer=secured, user_id=user_id)

@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    """
    Ask a question and get the answer
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    request_id = str(uuid.uuid4())
    logging.info(f"Request ID: {request_id}")
    
    
    try:
        return run_pipeline(request.question, request.user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {"message": "GenAI RAG Pipeline is running. Use POST /ask to ask a question"}

@app.get("/health")
async def health():
    """
    Health check endpoint
    """
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)