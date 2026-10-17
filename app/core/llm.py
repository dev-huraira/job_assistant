from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import get_settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


@lru_cache
def get_llm(temperature: float = 0.3) -> ChatGoogleGenerativeAI:
    """Create (once, cached) a Gemini chat model configured for this app."""
    settings = get_settings()

    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.google_api_key,
        temperature=temperature,
        timeout=30,
        max_retries=0,  # we handle retries ourselves, see call_llm below
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def invoke_with_retry(llm: ChatGoogleGenerativeAI, messages: list):
    """Call the LLM, retrying on failure with exponential backoff."""
    logger.debug("Calling LLM with %d message(s)", len(messages))
    return llm.invoke(messages)