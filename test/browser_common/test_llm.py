#!/usr/bin/env python3
"""Simple test cases for LLM modules - Only test actual model invocation"""

import pytest
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import LLM modules
from browser_common.llm import llm_deepseek, llm_qwen


class TestDeepSeekLLM:
    """Test cases for DeepSeek LLM module"""
    
    def test_deepseek_invoke(self):
        """Test DeepSeek LLM can be invoked"""
        llm = llm_deepseek.llm
        # Test actual model invocation
        result = llm.invoke("Briefly explain what a large model is.")
        print(f"DeepSeek response: {result}")
        assert result is not None

    def test_deepseek_async_invoke(self):
        """Test DeepSeek LLM can be invoked asynchronously"""
        llm = llm_deepseek.llm
        # Test actual async model invocation
        import asyncio
        result = asyncio.run(llm.ainvoke("What is machine learning?"))
        print(f"DeepSeek async response: {result}")
        assert result is not None


class TestQwenLLM:
    """Test cases for Qwen LLM module"""
    
    def test_qwen_invoke(self):
        """Test Qwen LLM can be invoked"""
        llm = llm_qwen.llm
        # Test actual model invocation
        result = llm.invoke("Briefly explain what a large model is.")
        print(f"Qwen response: {result}")
        assert result is not None
    
    def test_qwen_async_invoke(self):
        """Test Qwen LLM can be invoked asynchronously"""
        llm = llm_qwen.llm
        # Test actual async model invocation
        import asyncio
        result = asyncio.run(llm.ainvoke("What is artificial intelligence?"))
        print(f"Qwen async response: {result}")
        assert result is not None

if __name__ == "__main__":
    # Can run pytest directly
    pytest.main([__file__, "-v"])