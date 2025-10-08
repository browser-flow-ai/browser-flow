#!/usr/bin/env python3
"""Test cases for browser-control functionality - Extract, Observe, and Act"""

import asyncio
import pytest
import sys
import os
from pathlib import Path
from pydantic import BaseModel, Field

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from browser_control.agent_hand import AgentHand
from browser_common.browser_logging import get_logger

logger = get_logger("browser_control.test_demo", enable_file_logging=False)


class ContributorSchema(BaseModel):
    """Schema for contributor extraction."""
    username: str = Field(description="Contributor username")
    url: str = Field(description="Contributor profile URL")


class TestBrowserControlFunctionality:
    """Test cases for browser-control functionality"""

    @pytest.fixture
    async def agent(self):
        """Create an AgentHand instance for testing"""
        agent = AgentHand("test_browser_control")
        await agent.init()
        yield agent
        await agent.close()

    @pytest.mark.asyncio
    async def test_extract_functionality(self, agent):
        """Test extract functionality on books.toscrape.com"""
        await agent.goto("https://books.toscrape.com/")
        
        result = await agent.extract("Extract all book names, prices, and ratings")
        
        # Verify extraction result
        assert result is not None
        print(f"Extract result: {result}")
        
        # Test with schema-based extraction
        contributor_schema = await agent.extract({
            "instruction": "Extract book information",
            "output_schema": ContributorSchema
        })
        
        print(f"Schema-based extraction: {contributor_schema}")
        assert isinstance(contributor_schema, dict)

    @pytest.mark.asyncio
    async def test_observe_functionality(self, agent):
        """Test observe functionality on Google page"""
        await agent.goto("https://www.google.com/")
        
        # Wait for page to load
        await asyncio.sleep(3)
        
        result = await agent.observe("Find clickable buttons.")
        
        # Verify we got some results
        assert isinstance(result, list)
        print(f"Observe result: {result}")
        print(f"Found {len(result)} clickable elements")

    @pytest.mark.asyncio
    async def test_act_functionality(self, agent):
        """Test act functionality on Google page"""
        await agent.goto("https://www.google.com")
        
        # Test typing action
        await agent.act("type in 'Browserbase'")
        
        # Test press enter action
        await agent.act("press enter")

        # Wait for page to load
        await asyncio.sleep(3)
        
        print("Act functionality test completed successfully")

    @pytest.mark.asyncio
    async def test_combined_workflow(self, agent):
        """Test combined workflow: goto -> observe -> act -> extract"""
        # Navigate to a test page
        await agent.goto("https://books.toscrape.com/")
        
        # Observe the page
        observe_result = await agent.observe("Find book titles and prices")
        assert isinstance(observe_result, list)
        print(f"Observed {len(observe_result)} elements")
        
        # Extract information
        extract_result = await agent.extract("Extract book titles and prices")
        assert extract_result is not None
        print(f"Extracted: {extract_result}")
        
        # Act on the page (click on a book)
        await agent.act("click on the first book")
        
        # Extract more detailed information
        detailed_result = await agent.extract("Extract book details")
        assert detailed_result is not None
        print(f"Detailed extraction: {detailed_result}")

    @pytest.mark.asyncio
    async def test_error_handling(self, agent):
        """Test error handling in browser control operations"""
        # Test with invalid URL
        try:
            await agent.goto("https://invalid-url-that-does-not-exist.com")
        except Exception as e:
            print(f"Expected error for invalid URL: {e}")
        
        # Test with invalid action
        await agent.goto("https://www.google.com")
        try:
            await agent.act("perform impossible action")
        except Exception as e:
            print(f"Expected error for invalid action: {e}")

    @pytest.mark.asyncio
    async def test_multiple_pages(self, agent):
        """Test functionality across multiple pages"""
        # First page
        await agent.goto("https://www.google.com")
        google_result = await agent.observe("Find search elements")
        assert isinstance(google_result, list)
        
        # Second page
        await agent.goto("https://books.toscrape.com/")
        books_result = await agent.extract("Extract book information")
        assert books_result is not None
        
        # Third page
        await agent.goto("https://www.github.com")
        github_result = await agent.observe("Find navigation elements")
        assert isinstance(github_result, list)
        
        print("Successfully tested across multiple pages")

    @pytest.mark.asyncio
    async def test_schema_validation(self, agent):
        """Test schema-based extraction validation"""
        await agent.goto("https://books.toscrape.com/")
        
        # Test with ContributorSchema
        result = await agent.extract({
            "instruction": "Extract book information as contributor data",
            "output_schema": ContributorSchema
        })
        
        # Verify schema compliance - result should be a ContributorSchema instance
        assert isinstance(result, ContributorSchema)
        assert isinstance(result.username, str)
        assert isinstance(result.url, str)
        
        print(f"Schema validation result: {result}")


if __name__ == "__main__":
    # Can run pytest directly
    pytest.main([__file__, "-v", "-s"])
