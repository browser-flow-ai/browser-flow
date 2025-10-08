#!/usr/bin/env python3
"""Integration test cases for browser_wrapper using pytest"""

import pytest
import asyncio
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from browser_wrapper.stagehand import Stagehand


class TestBrowserWrapperIntegration:
    """Integration test cases for browser_wrapper module"""
    
    @pytest.mark.asyncio
    async def test_deepseek_website_accessibility_tree(self):
        """Test getting accessibility tree from DeepSeek website"""
        stagehand = Stagehand()
        await stagehand.init()
        page = stagehand.page
        
        # Navigate to DeepSeek website
        await page.goto("https://www.deepseek.com")
        await asyncio.sleep(3)
        
        # Get accessibility tree
        a_tree = await page.get_a11y_tree()
        
        # Verify the response structure
        assert a_tree is not None
        assert "combinedTree" in a_tree
        assert "combinedXpathMap" in a_tree
        assert "discoveredIframes" in a_tree
        
        # Print results for verification
        print("The A11 Tree:")
        combined_tree = a_tree["combinedTree"]
        combined_xpath_map = a_tree["combinedXpathMap"]
        discovered_iframes = a_tree["discoveredIframes"]
        
        print(f"Combined Tree: {combined_tree}")
        print(f"Combined XPath Map: {combined_xpath_map}")
        print(f"Discovered Iframes: {discovered_iframes}")
        
        # Basic assertions
        assert isinstance(combined_tree, str)  # combinedTree is a string representation
        assert isinstance(combined_xpath_map, dict)  # combinedXpathMap is a dictionary
        assert isinstance(discovered_iframes, list)  # discoveredIframes is a list
    
    @pytest.mark.asyncio
    async def test_stagehand_initialization(self):
        """Test Stagehand initialization"""
        stagehand = Stagehand()
        await stagehand.init()
        
        # Verify stagehand is properly initialized
        assert stagehand is not None
        assert stagehand.page is not None
        
        # Test basic page operations
        page = stagehand.page
        assert page is not None
    
    @pytest.mark.asyncio
    async def test_page_navigation(self):
        """Test basic page navigation functionality"""
        stagehand = Stagehand()
        await stagehand.init()
        page = stagehand.page
        
        # Test navigation to a simple page
        await page.goto("https://example.com")
        await asyncio.sleep(1)
        
        # Verify page loaded
        assert page.url is not None
        assert "example.com" in page.url


if __name__ == "__main__":
    # Can run pytest directly
    pytest.main([__file__, "-v", "-s"])
