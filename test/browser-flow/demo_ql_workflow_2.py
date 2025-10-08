"""Test QL workflow functionality - equivalent to test_ql_workflow.ts"""

import asyncio

from browser_flow.graph import create_initial_state
from browser_flow.registry import get_runnable_by_session, dispose_session

from browser_common.browser_logging import get_logger
logger = get_logger("browser_flow.test1", enable_file_logging=False)

async def run_react_workflow(user_message: str, max_steps: int = 10):
    """Run ReAct workflow - equivalent to runReActWorkflow function."""
    from datetime import datetime
    import time
    import os
    
    # Current local time
    now = datetime.now()
    # Common format: YYYY-MM-DD HH:MM:SS
    session_id = now.strftime("%Y-%m-%d-%H:%M:%S")
    
    # Setup logging

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

# Test graceful termination.
async def workflow_1():
    """Test startup and shutdown loop"""
    instruction = "Open Baidu, then close Baidu"
    try:
        result = await run_react_workflow(instruction, 10)
        return result
    except Exception as e:
        print(e)
        raise

# Test extraction results
async def workflow_2():
    """Test startup and shutdown loop"""
    instruction = "Open https://books.toscrape.com/ and extract book price and other information."
    try:
        result = await run_react_workflow(instruction, 10)
        return result
    except Exception as e:
        print(e)
        raise



if __name__ == "__main__":
    asyncio.run(workflow_2())
