#!/usr/bin/env python3
"""Test cases for Stagehand page context management functionality"""

import pytest
import asyncio
from pathlib import Path
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from browser_wrapper.stagehand import Stagehand
from browser_wrapper.stagehand_context import StagehandContext
from browser_wrapper.stagehand_page import StagehandPage


class TestStagehandPageContextManagement:
    """Test cases for Stagehand page context management"""

    @pytest.fixture
    async def stagehand_instance(self):
        """Create a Stagehand instance for testing"""
        stagehand = Stagehand()
        # Mock the browser initialization to avoid actual browser launch
        with patch('browser_wrapper.stagehand.get_browser') as mock_get_browser:
            mock_context = MagicMock()
            mock_context.new_page = AsyncMock()
            mock_context.add_init_script = AsyncMock()
            mock_context.new_cdp_session = AsyncMock()
            
            mock_browser_result = {
                "browser": MagicMock(),
                "context": mock_context,
                "debug_url": None,
                "session_url": None,
                "session_id": "test_session",
            }
            mock_get_browser.return_value = mock_browser_result
            
            # Mock the context creation
            with patch('browser_wrapper.stagehand_context.StagehandContext') as mock_context_class:
                mock_stagehand_context = MagicMock()
                mock_stagehand_context.get_stagehand_pages = AsyncMock(return_value=[])
                mock_stagehand_context._create_stagehand_page = AsyncMock()
                mock_stagehand_context.context = mock_context  # Set the context property
                mock_context_class.return_value = mock_stagehand_context
                
                await stagehand.init()
                yield stagehand
                await stagehand.close()

    @pytest.fixture
    def mock_playwright_page(self):
        """Create a mock Playwright page"""
        page = MagicMock()
        page.url = "https://example.com"
        page.title = AsyncMock(return_value="Test Page")
        page.goto = AsyncMock()
        page.wait_for_load_state = AsyncMock()
        page.evaluate = AsyncMock(return_value=False)
        page.add_init_script = AsyncMock()
        return page

    @pytest.fixture
    def mock_browser_context(self):
        """Create a mock browser context"""
        context = MagicMock()
        context.pages = []
        context.new_page = AsyncMock()
        context.add_init_script = AsyncMock()
        context.new_cdp_session = AsyncMock()
        context.on = MagicMock()
        return context

    @pytest.mark.asyncio
    async def test_stagehand_context_initialization(self, mock_browser_context):
        """Test StagehandContext initialization"""
        stagehand = MagicMock()
        stagehand._page_switch_lock = asyncio.Lock()
        
        context = StagehandContext(mock_browser_context, stagehand)
        
        assert context.stagehand == stagehand
        assert context._int_context == mock_browser_context
        assert context._active_stagehand_page is None
        assert len(context._page_map) == 0
        assert len(context._frame_id_map) == 0

    @pytest.mark.asyncio
    async def test_create_stagehand_page(self, mock_browser_context, mock_playwright_page):
        """Test creating a StagehandPage wrapper"""
        stagehand = MagicMock()
        stagehand._page_switch_lock = asyncio.Lock()
        
        context = StagehandContext(mock_browser_context, stagehand)
        
        # Mock StagehandPage creation
        with patch('browser_wrapper.stagehand_page.StagehandPage') as mock_page_class:
            mock_stagehand_page = MagicMock()
            mock_stagehand_page.init = AsyncMock(return_value=mock_stagehand_page)
            mock_page_class.return_value = mock_stagehand_page
            
            # Mock _attach_frame_navigated_listener
            with patch.object(context, '_attach_frame_navigated_listener', new_callable=AsyncMock):
                result = await context._create_stagehand_page(mock_playwright_page)
                
                assert result == mock_stagehand_page
                assert mock_playwright_page in context._page_map
                assert context._page_map[mock_playwright_page] == mock_stagehand_page

    @pytest.mark.asyncio
    async def test_set_active_page(self, mock_browser_context):
        """Test setting active page"""
        stagehand = MagicMock()
        stagehand._page_switch_lock = asyncio.Lock()
        stagehand._set_active_page = MagicMock()
        
        context = StagehandContext(mock_browser_context, stagehand)
        
        mock_stagehand_page = MagicMock()
        mock_stagehand_page.url = "https://example.com"
        
        context._set_active_page(mock_stagehand_page)
        
        assert context._active_stagehand_page == mock_stagehand_page
        stagehand._set_active_page.assert_called_once_with(mock_stagehand_page)

    @pytest.mark.asyncio
    async def test_new_page_creation(self, mock_browser_context):
        """Test creating new pages through context"""
        stagehand = MagicMock()
        stagehand._page_switch_lock = asyncio.Lock()
        
        context = StagehandContext(mock_browser_context, stagehand)
        
        # Mock new page creation
        mock_playwright_page = MagicMock()
        mock_browser_context.new_page.return_value = mock_playwright_page
        
        # Mock _create_stagehand_page
        mock_stagehand_page = MagicMock()
        with patch.object(context, '_create_stagehand_page', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_stagehand_page
            
            result = await context.new_page()
            
            assert result == mock_stagehand_page
            mock_browser_context.new_page.assert_called_once()
            mock_create.assert_called_once_with(mock_playwright_page)

    @pytest.mark.asyncio
    async def test_get_stagehand_pages(self, mock_browser_context):
        """Test getting all StagehandPage wrappers"""
        stagehand = MagicMock()
        stagehand._page_switch_lock = asyncio.Lock()
        
        context = StagehandContext(mock_browser_context, stagehand)
        
        # Mock existing pages
        mock_page1 = MagicMock()
        mock_page2 = MagicMock()
        mock_browser_context.pages = [mock_page1, mock_page2]
        
        # Mock get_stagehand_page
        mock_stagehand_page1 = MagicMock()
        mock_stagehand_page2 = MagicMock()
        
        with patch.object(context, 'get_stagehand_page', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [mock_stagehand_page1, mock_stagehand_page2]
            
            result = await context.get_stagehand_pages()
            
            assert len(result) == 2
            assert result[0] == mock_stagehand_page1
            assert result[1] == mock_stagehand_page2
            assert mock_get.call_count == 2

    @pytest.mark.asyncio
    async def test_handle_new_playwright_page(self, mock_browser_context):
        """Test handling new Playwright page creation"""
        stagehand = MagicMock()
        stagehand._page_switch_lock = asyncio.Lock()
        
        context = StagehandContext(mock_browser_context, stagehand)
        
        mock_playwright_page = MagicMock()
        mock_stagehand_page = MagicMock()
        
        # Mock _create_stagehand_page and _set_active_page
        with patch.object(context, '_create_stagehand_page', new_callable=AsyncMock) as mock_create:
            with patch.object(context, '_set_active_page') as mock_set_active:
                with patch.object(context, '_attach_frame_navigated_listener', new_callable=AsyncMock) as mock_attach:
                    mock_create.return_value = mock_stagehand_page
                    
                    await context._handle_new_playwright_page(mock_playwright_page)
                    
                    mock_create.assert_called_once_with(mock_playwright_page)
                    mock_set_active.assert_called_once_with(mock_stagehand_page)
                    mock_attach.assert_called_once_with(mock_playwright_page)

    @pytest.mark.asyncio
    async def test_frame_id_registration(self, mock_browser_context):
        """Test frame ID registration and retrieval"""
        stagehand = MagicMock()
        stagehand._page_switch_lock = asyncio.Lock()
        
        context = StagehandContext(mock_browser_context, stagehand)
        
        mock_stagehand_page = MagicMock()
        frame_id = "test_frame_123"
        
        # Test registration
        context.register_frame_id(frame_id, mock_stagehand_page)
        assert frame_id in context._frame_id_map
        assert context._frame_id_map[frame_id] == mock_stagehand_page
        
        # Test retrieval
        result = context.get_stagehand_page_by_frame_id(frame_id)
        assert result == mock_stagehand_page
        
        # Test unregistration
        context.unregister_frame_id(frame_id)
        assert frame_id not in context._frame_id_map

    @pytest.mark.asyncio
    async def test_stagehand_page_initialization(self, mock_playwright_page):
        """Test StagehandPage initialization"""
        stagehand = MagicMock()
        context = MagicMock()
        
        stagehand_page = StagehandPage(mock_playwright_page, stagehand, context)
        
        assert stagehand_page._page == mock_playwright_page
        assert stagehand_page._stagehand == stagehand
        assert stagehand_page._int_context == context
        assert stagehand_page._root_frame_id == ""
        assert stagehand_page._initialized is False

    @pytest.mark.asyncio
    async def test_stagehand_page_frame_id_management(self, mock_playwright_page):
        """Test StagehandPage frame ID management"""
        stagehand = MagicMock()
        context = MagicMock()
        
        stagehand_page = StagehandPage(mock_playwright_page, stagehand, context)
        
        # Test initial frame ID
        assert stagehand_page.frame_id == ""
        
        # Test updating frame ID
        new_frame_id = "new_frame_456"
        stagehand_page.update_root_frame_id(new_frame_id)
        assert stagehand_page.frame_id == new_frame_id

    @pytest.mark.asyncio
    async def test_stagehand_live_page_proxy(self, stagehand_instance):
        """Test Stagehand live page proxy functionality"""
        # Mock the page property to return a live proxy
        mock_page = MagicMock()
        stagehand_instance._page = mock_page
        
        # Test that page property returns LivePageProxy
        page_proxy = stagehand_instance.page
        assert page_proxy is not None
        assert hasattr(page_proxy, '_stagehand')

    @pytest.mark.asyncio
    async def test_popup_handling(self, mock_playwright_page):
        """Test popup window handling"""
        stagehand = MagicMock()
        context = MagicMock()
        
        stagehand_page = StagehandPage(mock_playwright_page, stagehand, context)
        
        # Test popup event handler
        mock_listener = MagicMock()
        
        with patch.object(stagehand_page._page, 'on') as mock_on:
            await stagehand_page._handle_on_event("popup", mock_listener)
            
            # Should call the page's on method
            mock_on.assert_called_once()

    @pytest.mark.asyncio
    async def test_page_switching_with_lock(self, mock_browser_context):
        """Test page switching with proper locking"""
        stagehand = MagicMock()
        stagehand._page_switch_lock = asyncio.Lock()
        
        context = StagehandContext(mock_browser_context, stagehand)
        
        mock_playwright_page = MagicMock()
        mock_playwright_page.url = "https://popup.com"
        
        # Mock _create_stagehand_page and _set_active_page
        mock_stagehand_page = MagicMock()
        
        with patch.object(context, '_create_stagehand_page', new_callable=AsyncMock) as mock_create:
            with patch.object(context, '_set_active_page') as mock_set_active:
                mock_create.return_value = mock_stagehand_page
                
                # Test _handle_new_page with lock
                await context._handle_new_page(mock_playwright_page)
                
                mock_create.assert_called_once_with(mock_playwright_page)
                mock_set_active.assert_called_once_with(mock_stagehand_page)

    @pytest.mark.asyncio
    async def test_multiple_pages_context_management(self, mock_browser_context):
        """Test managing multiple pages in context"""
        stagehand = MagicMock()
        stagehand._page_switch_lock = asyncio.Lock()
        
        context = StagehandContext(mock_browser_context, stagehand)
        
        # Create multiple mock pages
        mock_page1 = MagicMock()
        mock_page2 = MagicMock()
        mock_page3 = MagicMock()
        
        mock_stagehand_page1 = MagicMock()
        mock_stagehand_page2 = MagicMock()
        mock_stagehand_page3 = MagicMock()
        
        # Test adding pages to context
        context._page_map[mock_page1] = mock_stagehand_page1
        context._page_map[mock_page2] = mock_stagehand_page2
        context._page_map[mock_page3] = mock_stagehand_page3
        
        # Test getting specific page
        with patch.object(context, 'get_stagehand_page', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_stagehand_page2
            result = await context.get_stagehand_page(mock_page2)
            assert result == mock_stagehand_page2
        
        # Test active page management
        context._set_active_page(mock_stagehand_page3)
        assert context.get_active_page() == mock_stagehand_page3

    @pytest.mark.asyncio
    async def test_context_cleanup_and_error_handling(self, mock_browser_context):
        """Test context cleanup and error handling"""
        stagehand = MagicMock()
        stagehand._page_switch_lock = asyncio.Lock()
        
        context = StagehandContext(mock_browser_context, stagehand)
        
        # Test error handling in _handle_new_page
        mock_playwright_page = MagicMock()
        
        with patch.object(context, '_create_stagehand_page', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("Test error")
            
            # Should not raise exception, should handle gracefully
            await context._handle_new_page(mock_playwright_page)
            
            # Verify error was handled (no exception raised)
            assert True  # If we get here, error was handled

    @pytest.mark.asyncio
    async def test_stagehand_page_cdp_client_management(self, mock_playwright_page):
        """Test StagehandPage CDP client management"""
        stagehand = MagicMock()
        context = MagicMock()
        
        stagehand_page = StagehandPage(mock_playwright_page, stagehand, context)
        
        # Mock CDP session
        mock_cdp_session = MagicMock()
        mock_cdp_session.send = AsyncMock()
        
        # Mock the context.context.new_cdp_session call
        mock_context_context = MagicMock()
        mock_context_context.new_cdp_session = AsyncMock(return_value=mock_cdp_session)
        context.context = mock_context_context
        
        result = await stagehand_page.get_cdp_client(mock_playwright_page)
        
        assert result == mock_cdp_session
        assert mock_playwright_page in stagehand_page._cdp_clients
        assert stagehand_page._cdp_clients[mock_playwright_page] == mock_cdp_session

    @pytest.mark.asyncio
    async def test_frame_ordinal_management(self, mock_playwright_page):
        """Test frame ordinal management for encoding"""
        stagehand = MagicMock()
        context = MagicMock()
        
        stagehand_page = StagehandPage(mock_playwright_page, stagehand, context)
        
        # Test ordinal assignment
        ordinal1 = stagehand_page.ordinal_for_frame_id("frame1")
        ordinal2 = stagehand_page.ordinal_for_frame_id("frame2")
        ordinal3 = stagehand_page.ordinal_for_frame_id("frame1")  # Should be same as first
        
        assert ordinal1 == 1
        assert ordinal2 == 2
        assert ordinal3 == 1  # Should reuse existing ordinal
        
        # Test encoding with frame ID
        encoded = stagehand_page.encode_with_frame_id("frame1", 123)
        assert encoded == "1-123"
        
        # Test reset
        stagehand_page.reset_frame_ordinals()
        assert stagehand_page._fid_ordinals == {None: 0}


if __name__ == "__main__":
    # Can run pytest directly
    pytest.main([__file__, "-v", "-s"])
