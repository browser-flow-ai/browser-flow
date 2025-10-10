import asyncio

from browser_control.agent_hand import AgentHand

async def get_scroll_position(agent):
    """获取当前滚动位置"""
    try:
        scroll_info = await agent.stagehand.page.page.evaluate("""
            () => {
                const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                const windowHeight = window.innerHeight;
                const documentHeight = document.documentElement.scrollHeight;
                const scrollPercent = Math.round((scrollTop / (documentHeight - windowHeight)) * 100);
                return { scrollTop, scrollPercent, windowHeight, documentHeight };
            }
        """)
        return scroll_info
    except Exception as e:
        print(f"Error getting scroll position: {e}")
        return None

async def scroll():
    agent = AgentHand("test_browser_control")
    await agent.init()
    
    print("Browser initialized, navigating to test page...")
    await agent.goto("https://infinite-scroll.com/demo/full-page/")
    await asyncio.sleep(3)
    
    # 获取初始滚动位置
    initial_position = await get_scroll_position(agent)
    print(f"Initial scroll position: {initial_position}")
    
    print("Starting scroll tests...")
    
    # Test 1: Scroll to next chunk
    print("\n=== Test 1: Scroll to next chunk ===")
    before = await get_scroll_position(agent)
    print(f"Before: scrollTop={before['scrollTop']}, scrollPercent={before['scrollPercent']}%")
    
    result1 = await agent.act("scroll to next chunk")
    print(f"Result 1: {result1}")
    
    await asyncio.sleep(3)
    after = await get_scroll_position(agent)
    print(f"After: scrollTop={after['scrollTop']}, scrollPercent={after['scrollPercent']}%")
    print(f"Change: {after['scrollTop'] - before['scrollTop']}px")

    # Test 2: Scroll to previous chunk  
    print("\n=== Test 2: Scroll to previous chunk ===")
    before = await get_scroll_position(agent)
    print(f"Before: scrollTop={before['scrollTop']}, scrollPercent={before['scrollPercent']}%")
    
    result2 = await agent.act("scroll to previous chunk")
    print(f"Result 2: {result2}")
    
    await asyncio.sleep(3)
    after = await get_scroll_position(agent)
    print(f"After: scrollTop={after['scrollTop']}, scrollPercent={after['scrollPercent']}%")
    print(f"Change: {after['scrollTop'] - before['scrollTop']}px")

    # Test 3: Scroll to 50%
    print("\n=== Test 3: Scroll to 50% ===")
    before = await get_scroll_position(agent)
    print(f"Before: scrollTop={before['scrollTop']}, scrollPercent={before['scrollPercent']}%")
    
    result3 = await agent.act("scroll to 50%")
    print(f"Result 3: {result3}")
    
    await asyncio.sleep(3)
    after = await get_scroll_position(agent)
    print(f"After: scrollTop={after['scrollTop']}, scrollPercent={after['scrollPercent']}%")
    print(f"Change: {after['scrollTop'] - before['scrollTop']}px")

    # Test 4: Scroll into view
    print("\n=== Test 4: Scroll into view ===")
    before = await get_scroll_position(agent)
    print(f"Before: scrollTop={before['scrollTop']}, scrollPercent={before['scrollPercent']}%")
    
    result4 = await agent.act("scroll into view")
    print(f"Result 4: {result4}")
    
    await asyncio.sleep(3)
    after = await get_scroll_position(agent)
    print(f"After: scrollTop={after['scrollTop']}, scrollPercent={after['scrollPercent']}%")
    print(f"Change: {after['scrollTop'] - before['scrollTop']}px")

    print("\n=== Scroll test completed ===")

if __name__ == "__main__":
    asyncio.run(scroll())