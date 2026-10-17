import sys

import fastapi
import langgraph
import langchain
import pydantic

print("Python version:", sys.version)
print("FastAPI:", fastapi.__version__)
print("Pydantic:", pydantic.VERSION)
print("LangChain:", langchain.__version__)
print("LangGraph imported OK")
print("Setup is working!")