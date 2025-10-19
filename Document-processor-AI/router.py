# generate the prompt and use it for next step
from config import DEFAULT_MODEL
TEMPLATE=""" You are a helpful assistant that can answer questions as best as you can:
{context}

Question: {question}

Answer: """

def build_prompt(question: str,context: str) -> tuple[str, str]:
    context_block = f"Context:\n {context}" if context.strip() else ""
    return DEFAULT_MODEL,TEMPLATE.format(context=context_block, question=question)