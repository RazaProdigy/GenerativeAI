#logging and observability module
import logging
from prometheus_client import start_http_server, Counter, Histogram

# metrics
REQUEST_COUNTER = Counter("genai_requests_total", "Total number of requests received")
LLM_LATENCY = Histogram("genai_llm_latency_ms", "LLM call latency in milliseconds")
RETRIEVAL_LATENCY = Histogram("genai_retrieval_latency_ms", "Retrieval latency in milliseconds")

def log(question, model_input,model_output, guardrail_output=None, model="unknown", latency_ms=None, user_id =None, retrieved_context=None):

    REQUEST_COUNTER.inc()

    logging.info("---------AUDIT LOG---------")
    logging.info(f"User ID: {user_id}") # user id is not used in the pipeline but it is good to have it
    logging.info(f"Question: {question}")
    logging.info(f"Model Input: {model_input}")
    logging.info(f"Model Output: {model_output}")
    if guardrail_output:
        logging.info(f"Guardrail Output: {guardrail_output}")
    logging.info(f"Model: {model}")
    logging.info(f"Latency: {latency_ms}ms")
    
    logging.info(f"Retrieved Context: {retrieved_context}")

def record_metric(metric_name, value):
    if metric_name == "llm_latency_ms":
        LLM_LATENCY.observe(value)
    elif metric_name == "retrieval_latency_ms":
        RETRIEVAL_LATENCY.observe(value)

def start_metrics_server(port=8000):
    start_http_server(port)
    logging.info(f" Prometheus Metrics server started on port {port}, at link http://localhost:{port}/metrics")