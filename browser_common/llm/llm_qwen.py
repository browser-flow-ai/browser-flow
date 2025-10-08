import os
from langchain_community.chat_models import ChatTongyi
from dotenv import load_dotenv

load_dotenv()

llm = ChatTongyi(  # Some versions are also called qwen ChatDashScope
    model="qwen-plus",  # For example: qwen-turbo, qwen-plus, qwen-max, qwen2-7b-instruct, etc.
    api_key=os.environ["DASHSCOPE_API_KEY"],
)
