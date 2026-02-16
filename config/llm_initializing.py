from langchain_openai import ChatOpenAI
from .configurable import config
import os
from dotenv import load_dotenv


load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY is not set. Please add it to your environment or a .env file "
        "in the project root before running the application."
    )

# Deep Think LLM
deep_think_llm = ChatOpenAI(
    model=config["deep_think_llm"],
    base_url=config["backend_url"],
    api_key=OPENAI_API_KEY,
    temperature=0.1,
)

# Quick Think LLM
quick_think_llm = ChatOpenAI(
    model=config["quick_think_llm"],
    base_url=config["backend_url"],
    api_key=OPENAI_API_KEY,
    temperature=0.1,
)

print("LLMs Initialized Successfully:")
print("--------------------------------")
print(f"Deep Think LLM: {deep_think_llm}")
print(f"Quick Think LLM: {quick_think_llm}")