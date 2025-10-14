"""Run simple graph example"""
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from browser_graph import create_simple_graph
from browser_common.browser_logging import get_logger

# Load environment variables
load_dotenv()

logger = get_logger("browser_graph.examples", enable_file_logging=False)


def main():
    """Run example"""
    logger.info("=" * 50)
    logger.info("Starting LangGraph simple example")
    logger.info("=" * 50)
    
    # Create graph
    graph = create_simple_graph()
    
    # Test messages
    test_messages = [
        "Hello!",
        "Please calculate 15 + 27",
        "Now calculate 8 * 6",
        "Please calculate 10 + 5 first, then multiply the result by 3",
    ]
    
    for msg in test_messages:
        logger.info(f"\n{'=' * 50}")
        logger.info(f"User input: {msg}")
        logger.info(f"{'=' * 50}")
        
        # Run graph
        result = graph.invoke({
            "messages": [HumanMessage(content=msg)]
        })
        
        # Print result
        final_message = result["messages"][-1]
        logger.info(f"Assistant reply: {final_message.content}")
    
    logger.info(f"\n{'=' * 50}")
    logger.info("Example completed")
    logger.info(f"{'=' * 50}")


if __name__ == "__main__":
    main()
