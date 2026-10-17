from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm import get_llm, invoke_with_retry
from app.core.logging_config import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

llm = get_llm(temperature=0.3)

messages = [
    SystemMessage(content="You are a concise assistant."),
    HumanMessage(content="Reply with exactly the word: OK"),
]

response = invoke_with_retry(llm, messages)

logger.info("Response type: %s", type(response).__name__)
logger.info("Response content: %s", response.content)
print("LLM call succeeded!")