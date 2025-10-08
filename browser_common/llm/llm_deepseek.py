"""LLM configuration for web2str Python implementation."""

import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# Create LLM instance directly, consistent with TypeScript version
llm = ChatOpenAI(
    model="deepseek-chat",
    temperature=0.1,
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1",
)
