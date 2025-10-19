# Orchestration of the full pipeline with observability and guardrails.
import time
import argparse
import logging

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s",
                    handlers=[logging.FileHandler("pipeline.log"),
                              logging.StreamHandler()])

from cache_store import get as cache_get, set as cache_set
from retrieval import retrieve_context
from router import build_prompt
from llm_client import call as llm_call
from postprocess import secure_output
from config import CACHE_TTL_SECONDS, CACHE_SIMILARITY_THRESHOLD
from guardrails import apply_guardrails
from observability import log, record_metric, start_metrics_server

start_metrics_server()

def run_pipeline(question: str):
    logging.info(f"Starting pipeline for question: {question}")
    #step 1 : Check cache with semantic similarity
    cached = cache_get(question, similarity_threshold=CACHE_SIMILARITY_THRESHOLD)
    if cached:
        logging.info(f"Semantic cache hit for question: {question}")
        return cached
    
    #step 2 : Retrieve context
    start_retrieve = time.time()
    context = retrieve_context(question)
    retrival_latency = int( (time.time() - start_retrieve)*1000) # in milliseconds
    logging.info(f"Retrieval latency: {retrival_latency}ms")
    logging.info("Retrieved context:")
    record_metric("retrieval_latency_ms", retrival_latency)
    logging.info(context)
    
    # step 3 : Route Prompt to model
    model, prompt = build_prompt(question, context)
    logging.info("Assembled prompt:")
    logging.info(prompt)

    
    # step 4 : Call LLM
    start_llm = time.time()
    answer = llm_call(model, prompt)
    llm_latency = int( (time.time() - start_llm)*1000) # in milliseconds
    logging.info(f"LLM latency: {llm_latency}ms")
    record_metric("llm_latency_ms", llm_latency)

    post_processed = secure_output(answer)

    # step 5 : Apply guardrails
    secured = apply_guardrails(post_processed)

    #observability logs
    log(question, prompt, post_processed,secured , model=model, latency_ms=retrival_latency + llm_latency, retrieved_context=context)

    cache_set(question, secured, CACHE_TTL_SECONDS)
    logging.info(f"Cached answer for question: {question}")
    return secured

if __name__ == "__main__":
    start_metrics_server(port=8002)
    parser = argparse.ArgumentParser(description="Run the GEN AI RAG pipeline")
    parser.add_argument("--question", type=str, required=True, help="The question to answer")
    args = parser.parse_args()
    response = run_pipeline(args.question)
    print(f"Response: {response}")  
    # Keep metrics server running
    print("Pipeline execution completed.Keeping the metrics server running...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Metrics server stopped.")
        exit(0)

# python main.py --question "What is Agentic AI?"