# logic for guardrails
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BANNED_WORDS = {"kill", "bomb","attack","shoot"}

# PII PATTERNS

PII_PATTERNS = [
    (r"\b\d{12}\b", "[REDACTED_AADHAAR]"), # aadhaar
    (r"\b\d{10}\b", "[REDACTED_PHONE]"), # Phone number
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[REDACTED_EMAIL]") # email
]

def apply_guardrails(text: str) -> str:
    """
    Apply guardrails to the text
    """
    original_text = text
    # 1. Check for banned words
    for word in BANNED_WORDS:
        if word.lower() in text.lower():
            logger.warning(f"Banned word found: {word}")
            text = text.replace(word, "BANNED_CONTENT")
            
    # 2. Check for PII
    for pattern, replacement in PII_PATTERNS:
        text = re.sub(pattern, replacement, text)
    
    if original_text != text:
        logger.info("Guardrails modified the output")
    
    else:
        logging.info("Guardrails did not modify the output")
    
    return text