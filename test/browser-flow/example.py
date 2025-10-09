"""Browser Flow Usage Examples"""

import asyncio
from browser_flow import BrowserFlow, run_workflow


async def example_1():
    """Example 1: Using BrowserFlow Class"""
    print("=== Example 1: Using BrowserFlow Class ===")
    
    # Create BrowserFlow instance
    flow = BrowserFlow()
    
    try:
        # Execute browser automation task
        result = await flow.run("Open Baidu, then close Baidu", max_steps=5)
        print(f"Execution result: {result}")
    except Exception as e:
        print(f"Execution error: {e}")
    finally:
        # Manually cleanup resources (optional, __del__ will auto cleanup)
        await flow.close()


async def example_2():
    """Example 2: Using Convenience Function"""
    print("\n=== Example 2: Using Convenience Function ===")
    
    try:
        # Use convenience function with automatic resource management
        result = await run_workflow(
            "Open https://books.toscrape.com/ and extract book price information", 
            max_steps=10
        )
        print(f"Execution result: {result}")
    except Exception as e:
        print(f"Execution error: {e}")


async def main():
    """Main function"""
    print("🚀 Browser Flow Usage Examples")
    print("=" * 50)
    
    # Run example 1
    await example_1()
    
    # Run example 2  
    await example_2()
    
    print("\n✅ All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
