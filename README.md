# Browser-Flow

A modern browser automation integration toolkit designed for developers and automation enthusiasts.

[中文版](README_CN.md) | [English](README.md)

## Project Overview

Browser-Flow is a modular browser automation solution that breaks down complex browser operations into multiple independent and composable components. Each component can be used standalone or in combination, providing developers with flexible and powerful browser automation capabilities.

## Core Components

- **[browser-common](browser-common)** - Core dependency library providing common browser operation interfaces
- **[browser-control](/browser-control)** - LLM-powered intelligent browser operation engine
- **[browser-flow](/browser-flow)** - Customizable browser workflow orchestration system
- **[browser-wrapper](/browser-wrapper)** - Browser wrapper layer for A11y Tree access

## Quick Start

### Prerequisites

- Python 3.13+
- Poetry (package manager)

### Installation Steps

1. **Check Python Environment**
   ```bash
   poetry env list
   poetry env use 3.13
   poetry run python --version
   ```

2. **Install Dependencies**
   ```bash
   poetry install
   poetry run playwright install chromium
   ```

3. **Add New Packages** (if needed)
   ```bash
   poetry add pydantic-ai
   ```

## Usage

Browser-Flow provides a simple and easy-to-use wrapper class that allows you to quickly start browser automation tasks.

### Basic Usage

#### Method 1: Using BrowserFlow Class

```python
import asyncio
from browser_flow import BrowserFlow

async def main():
    # Create BrowserFlow instance
    flow = BrowserFlow()
    
    try:
        # Execute browser automation task
        result = await flow.run("Open Baidu, then close Baidu", max_steps=5)
        print(f"Execution result: {result}")
    except Exception as e:
        print(f"Execution error: {e}")
    finally:
        # Manually cleanup resources
        await flow.close()

# Run example
asyncio.run(main())
```

#### Method 2: Using Convenience Function (Recommended)

```python
import asyncio
from browser_flow import run_workflow

async def main():
    try:
        # Use convenience function with automatic resource management
        result = await run_workflow(
            "Open https://books.toscrape.com/ and extract book price information", 
            max_steps=10
        )
        print(f"Execution result: {result}")
    except Exception as e:
        print(f"Execution error: {e}")

# Run example
asyncio.run(main())
```

### Parameter Description

- `instruction`: Browser automation instruction (string)
- `max_steps`: Maximum execution steps (default: 10)
- `session_id`: Optional session ID (auto-generated)

### More Examples

Check the [browser_flow/example.py](browser_flow/example.py) file for more usage examples.

### Advanced Usage: Direct browser-control

If you need more fine-grained control, you can use the `browser-control` module directly:

```python
import asyncio
from browser_control.agent_hand import AgentHand
from pydantic import BaseModel, Field

# Define data extraction schema
class BookSchema(BaseModel):
    """Book information schema"""
    title: str = Field(description="Book title")
    price: str = Field(description="Book price")
    rating: str = Field(description="Book rating")

async def advanced_example():
    """Advanced usage example"""
    # Create AgentHand instance
    agent = AgentHand("advanced_example")
    
    try:
        await agent.init()
        
        # 1. Navigate to webpage
        await agent.goto("https://books.toscrape.com/")
        
        # 2. Observe page elements
        elements = await agent.observe("Find book titles and prices")
        print(f"Found {len(elements)} elements")
        
        # 3. Extract information (text mode)
        result = await agent.extract("Extract all book names, prices, and ratings")
        print(f"Extraction result: {result}")
        
        # 4. Extract information (structured schema)
        structured_result = await agent.extract({
            "instruction": "Extract book information",
            "output_schema": BookSchema
        })
        print(f"Structured extraction result: {structured_result}")
        
        # 5. Perform actions
        await agent.act("click on the first book")
        
        # 6. Extract detailed information
        details = await agent.extract("Extract book details")
        print(f"Detailed information: {details}")
        
    except Exception as e:
        print(f"Execution error: {e}")
    finally:
        await agent.close()

# Run example
asyncio.run(advanced_example())
```

### browser-control Core Methods

- **`goto(url)`**: Navigate to specified URL
- **`observe(instruction)`**: Observe page elements, returns actionable element list
- **`extract(instruction)`**: Extract page information
- **`extract(schema_dict)`**: Extract information using structured schema
- **`act(instruction)`**: Execute browser actions (click, type, press keys, etc.)

## Key Features

- 🚀 **Modular Design** - Each component runs independently, use as needed
- 🤖 **AI-Powered** - Integrated with large language models for intelligent browser operations
- 🔧 **Highly Customizable** - Support for custom workflows and operation logic
- 📱 **Accessibility Support** - Built-in A11y Tree support for enhanced accessibility
- 🛡️ **Stable & Reliable** - Built on the mature Playwright framework

## Technical Notes

> **Important**: This project draws inspiration from many excellent designs in Stagehand, but has been deeply optimized to address compatibility issues between the Python and TypeScript versions, resolving problems that existed in the original implementation.

## Contributing

We welcome all forms of contributions! If you'd like to contribute to the project:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

If you have questions or suggestions, please contact us through:

- Submit an [Issue](../../issues)
- Start a [Discussion](../../discussions)

---

**Browser-Flow** - Making browser automation simple and powerful!
