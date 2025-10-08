"""Test QL workflow functionality - equivalent to test_ql_workflow.ts"""

import asyncio
import os

from browser_common.browser_logging import get_logger
from browser_flow.graph import create_initial_state
from browser_flow.registry import get_runnable_by_session, dispose_session

logger = get_logger("browser_flow.test", enable_file_logging=False)

async def run_react_workflow(user_message: str, max_steps: int = 10):
    """Run ReAct workflow - equivalent to runReActWorkflow function."""
    from datetime import datetime
    import time
    import os
    
    # Current local time
    now = datetime.now()
    # Common format: YYYY-MM-DD HH:MM:SS
    session_id = now.strftime("%Y-%m-%d-%H:%M:%S")
    

    # Display current working directory and log file locations
    current_dir = os.getcwd()
    logs_dir = os.path.join(current_dir, "logs")
    state_log_file = os.path.join(logs_dir, f"state_updates_{session_id}.jsonl")
    a11y_log_file = os.path.join(logs_dir, f"a11y_tree_{session_id}.jsonl")
    
    print(f"📁 Current working directory: {current_dir}")
    print(f"📁 Log directory: {logs_dir}")
    print(f"📄 State log file: {state_log_file}")
    print(f"📄 A11y tree log file: {a11y_log_file}")
    print("")
    
    try:
        # Get graph instance
        logger.info("🔧 Getting workflow graph instance...")
        graph = await get_runnable_by_session(session_id)
        logger.info("✅ Workflow graph instance obtained successfully")
        
        # Create initial state
        logger.info("🔧 Creating initial state...")
        initial_state = create_initial_state(session_id, user_message, max_steps)
        logger.info("✅ Initial state created successfully")

        logger.info("🚀 Starting LangGraph workflow execution...")
        logger.info("⏳ Note: DeepSeek API calls may take a long time, please be patient...")
        
        start_time = time.time()
        result = await graph.ainvoke(initial_state)
        end_time = time.time()
        
        execution_time = end_time - start_time
        logger.info(f"⏱️ Workflow execution completed, time taken: {execution_time:.2f} seconds")
        
        # Check if log files were created successfully
        state_log_exists = os.path.exists(state_log_file)
        a11y_log_exists = os.path.exists(a11y_log_file)
        
        print(f"📊 Log file creation status:")
        print(f"  State log: {'✅ Created' if state_log_exists else '❌ Not created'}")
        print(f"  A11y tree log: {'✅ Created' if a11y_log_exists else '❌ Not created'}")
        
        if state_log_exists:
            state_log_size = os.path.getsize(state_log_file)
            print(f"  State log size: {state_log_size} bytes")
        
        if a11y_log_exists:
            a11y_log_size = os.path.getsize(a11y_log_file)
            print(f"  A11y tree log size: {a11y_log_size} bytes")

        return result
        
    except Exception as error:
        raise error
    finally:
        # Ensure cleanup of browser resources
        try:
            logger.info("🗑️ Cleaning up browser resources...")
            await dispose_session(session_id)
            logger.info("✅ Browser resources cleanup completed")
        except Exception as cleanup_error:
            logger.warning(f"⚠️ Warning during resource cleanup: {cleanup_error}")

async def workflow_3():
    """Test startup and shutdown closed loop"""
    instruction = "Open Baidu, then close Baidu"
    try:
        result = await run_react_workflow(instruction, 10)
        return result
    except Exception as e:
        print(e)
        raise


async def workflow_2():
    """Test workflow for Trump activities."""
    instruction = "What activities did Trump participate in and how were they evaluated?"
    logger.info(f"🎯 Starting workflow: Trump activity query")
    logger.info(f"📝 Task description: {instruction}")
    logger.info("⚠️ Note: This task requires searching network information and may take a long time")
    
    try:
        result = await run_react_workflow(instruction, 10)
        logger.info(f"📊 Trump activity query results: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ Trump activity query failed: {e}")
        raise

async def workflow_1():
    """Test workflow for AI company funding."""
    instruction = "Find AI companies that have recently received funding, the investment amount and links."
    logger.info(f"🎯 Starting workflow: AI company funding query")
    logger.info(f"📝 Task description: {instruction}")
    logger.info("⚠️ Note: This task requires searching network information and may take a long time")
    
    try:
        result = await run_react_workflow(instruction, 10)
        logger.info(f"📊 AI company funding query results: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ AI company funding query failed: {e}")
        raise

async def workflow_amazon_shoes():
    """Test workflow for Amazon shoes search."""
    instruction = "Find the cheapest 10 pairs of sports shoes on Amazon."
    logger.info(f"🎯 Starting workflow: Amazon sports shoes search")
    logger.info(f"📝 Task description: {instruction}")
    logger.info("⚠️ Note: This task requires accessing Amazon website, please ensure network connection is normal")
    logger.info("🔍 Tip: If you encounter a selection page, please choose the first option to enter Amazon homepage")
    
    try:
        result = await run_react_workflow(instruction, 15)  # Increase maximum steps
        logger.info(f"📊 Amazon sports shoes search results: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ Amazon sports shoes search failed: {e}")
        raise

async def workflow_amazon_simple():
    """Test workflow for simple Amazon navigation."""
    instruction = "Go to Amazon website homepage"
    logger.info(f"🎯 Starting workflow: Amazon simple navigation")
    logger.info(f"📝 Task description: {instruction}")
    logger.info("ℹ️ This is a simple website navigation task")
    logger.info("🔍 Tip: If you encounter 'Click the button below to continue shopping', please click that button")
    
    try:
        result = await run_react_workflow(instruction, 10)  # Increase steps
        logger.info(f"📊 Amazon navigation results: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ Amazon navigation failed: {e}")
        raise


async def workflow_baidu():
    """Test workflow for opening Baidu."""
    instruction = "Open Baidu"
    logger.info(f"🎯 Starting workflow: Open Baidu")
    logger.info(f"📝 Task description: {instruction}")
    logger.info("ℹ️ This is a simple web navigation task")
    
    try:
        result = await run_react_workflow(instruction, 5)
        logger.info(f"📊 Baidu opening results: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ Baidu opening failed: {e}")
        raise


async def workflow_baidu_refresh():
    """Test workflow for opening Baidu and refreshing."""
    instruction = "Open Baidu, then refresh"
    logger.info(f"🎯 Starting workflow: Baidu open and refresh")
    logger.info(f"📝 Task description: {instruction}")
    logger.info("ℹ️ This is a web navigation and refresh task")
    
    try:
        result = await run_react_workflow(instruction, 5)
        logger.info(f"📊 Baidu refresh results: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ Baidu refresh failed: {e}")
        raise


async def workflow_baidu_wait_close():
    """Test workflow for opening Baidu, waiting, and closing."""
    instruction = "Enter Baidu, wait 100 seconds, then close"
    logger.info(f"🎯 Starting workflow: Baidu wait and close")
    logger.info(f"📝 Task description: {instruction}")
    logger.info("⚠️ Note: This task includes 100 seconds wait time, total execution time is long")
    
    try:
        result = await run_react_workflow(instruction, 5)
        logger.info(f"📊 Baidu wait and close results: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ Baidu wait and close failed: {e}")
        raise


async def workflow_baidu_navback():
    """Test workflow for opening Baidu, going back, and closing."""
    instruction = "Enter Baidu, go back, then close"
    logger.info(f"🎯 Starting workflow: Baidu go back and close")
    logger.info(f"📝 Task description: {instruction}")
    logger.info("ℹ️ This is a web navigation, go back and close task")
    
    try:
        result = await run_react_workflow(instruction, 5)
        logger.info(f"📊 Baidu go back and close results: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ Baidu go back and close failed: {e}")
        raise


async def main():
    """Run all workflow tests."""
    # Check environment variables
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("❌ Error: Please set DEEPSEEK_API_KEY environment variable")
        print("   For example: export DEEPSEEK_API_KEY='your_api_key_here'")
        return
    
    # Setup global logging
    logger.info("🚀 Starting QL workflow functionality test")
    print("=== Testing QL Workflow Functionality ===")
    print("⚠️ Note: DeepSeek API calls during testing may take a long time, please be patient")
    print("📋 If you encounter unexpected web pages, the system will automatically try to continue")
    print("")

    # Define test cases - first only test Amazon simple navigation
    test_cases = [
        {
            "name": "Find the cheapest sports shoes on Amazon",
            "function": workflow_amazon_shoes,
            "description": "Shoe collection task"
        }
        # {
        #     "name": "Amazon simple navigation test",
        #     "function": workflow_amazon_simple,
        #     "description": "Simple Amazon website navigation task"
        # },
        # {
        #     "name": "Trump activity query test",
        #     "function": workflow_2,
        #     "description": "Network information search task"
        # },
        # {
        #     "name": "AI company funding query test",
        #     "function": workflow_1,
        #     "description": "Network information search task"
        # },
        # {
        #     "name": "Baidu opening test",
        #     "function": workflow_baidu,
        #     "description": "Simple web navigation task"
        # },
        # {
        #     "name": "Baidu refresh test", 
        #     "function": workflow_baidu_refresh,
        #     "description": "Web navigation and refresh task"
        # },
        # {
        #     "name": "Baidu wait and close test",
        #     "function": workflow_baidu_wait_close,
        #     "description": "Task with long wait time"
        # },
        # {
        #     "name": "Baidu go back and close test",
        #     "function": workflow_baidu_navback,
        #     "description": "Web navigation, go back and close task"
        # }
    ]

    success_count = 0
    total_count = len(test_cases)

    try:
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"📋 Starting test case {i}/{total_count}: {test_case['name']}")
            logger.info(f"📝 Test description: {test_case['description']}")
            print(f"\n--- Test {i}/{total_count}: {test_case['name']} ---")
            
            try:
                result = await test_case['function']()
                success_count += 1
                logger.info(f"✅ Test case {i} executed successfully: {test_case['name']}")
                print(f"✅ Test {i} completed")
                
            except Exception as e:
                logger.error(f"❌ Test case {i} execution failed: {test_case['name']} - {e}")
                print(f"❌ Test {i} failed: {e}")
                # Continue to next test case, do not interrupt entire test flow
                continue

        # Output test results summary
        logger.info(f"📊 Test results summary: {success_count}/{total_count} test cases successful")
        print(f"\n=== Test Results Summary ===")
        print(f"✅ Success: {success_count}/{total_count}")
        print(f"❌ Failed: {total_count - success_count}/{total_count}")
        
        if success_count == total_count:
            logger.info("🎉 All workflow tests completed!")
            print("🎉 All tests completed!")
        else:
            logger.warning(f"⚠️ Some tests failed, please check logs for details")
            print("⚠️ Some tests failed, please check logs for details")

    except Exception as e:
        print(f"❌ Test flow failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(workflow_3())
