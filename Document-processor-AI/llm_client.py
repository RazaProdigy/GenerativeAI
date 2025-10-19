# llm block for prediction
import logging
from functools import lru_cache
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from config import TEMPERATURE, MAX_TOKENS,OPENAI_API_KEY

if OPENAI_API_KEY is None:
    raise RuntimeError("OPENAI_API_KEY is not set")

@lru_cache(maxsize=4)
def _get_chat(model_name:str) -> ChatOpenAI:
    logging.info(f"Initializing LLM client for {model_name}")
    return ChatOpenAI(
        model=model_name,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        openai_api_key=OPENAI_API_KEY,
    )

def call(model:str, prompt: str) -> str:
    # prompt --> assembled prompt from router.py
    # model --> model name from router.py
    logging.info(f"Calling {model} with prompt: {prompt}")
    chat = _get_chat(model)
    response: AIMessage = chat.invoke(prompt)
    logging.info(f"Response: {response.content}")
    return response.content.strip()
