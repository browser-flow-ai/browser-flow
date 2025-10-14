# Quick Start Guide

## Get Started in 5 Minutes

### 1️⃣ Environment Setup

```bash
# Activate Poetry virtual environment
source /Users/farmer/Library/Caches/pypoetry/virtualenvs/agentql-kwV3nYNt-py3.13/bin/activate
```

Ensure `DEEPSEEK_API_KEY` is configured in the project root's `.env` file.

### 2️⃣ Run Example

```bash
# Method 1: Use quick start script
./browser_graph/examples/run.sh

# Method 2: Manual run
cd browser-flow
python -m browser_graph.examples.run_simple_graph
```

### 3️⃣ Expected Output

```
==================================================
Starting LangGraph simple example
==================================================

User input: Hello!
Reasoning: The user is just saying hello...
Direct answer: Hello! How can I help you today?

User input: Please calculate 15 + 27
Tool to call: add
Executing addition: 15 + 27
Result: 42
Assistant reply: The sum of 15 and 27 is 42.

User input: Now calculate 8 * 6
Tool to call: multiply
Executing multiplication: 8 * 6
Result: 48
Assistant reply: 8 multiplied by 6 is 48.
```

## Core Concepts

### 🏗️ Project Structure

```
handlers/     → Business logic (pure functions)
    ↓
tools/        → Wrapped as StructuredTool
    ↓
nodes/        → Agent and Tool nodes
    ↓
graph/        → Organized as workflow
```

### 🔄 Workflow

```
User Input
  ↓
Agent Node (Analysis + Decision)
  ↓
Need Tool?
  ├─ Yes → Tool Node (Execute) → Agent Node (Answer)
  └─ No → Direct Answer
```

### 💡 DeepSeek Features

- ❌ **Not Supported**: `llm.bind_tools()` 
- ✅ **Use**: Prompt engineering + JSON output
- ✅ **Advantage**: Highly controllable, flexible customization

## Add New Tool (3 Steps)

### Step 1: Implement Handler

```python
# browser_graph/handlers/weather.py
def get_weather(city: str) -> str:
    """Get weather information"""
    return f"The weather in {city} is sunny"
```

### Step 2: Wrap as Tool

```python
# browser_graph/tools/weather_tools.py
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

class WeatherInput(BaseModel):
    city: str = Field(description="City name")

weather_tool = StructuredTool.from_function(
    func=get_weather,
    name="get_weather",
    description="Get weather information for a specified city",
    args_schema=WeatherInput,
)
```

### Step 3: Add to Tool List

```python
# browser_graph/tools/calculator_tools.py
from browser_graph.tools.weather_tools import weather_tool

all_tools = [add_tool, multiply_tool, weather_tool]
```

Done! The Agent can now query weather.

## Create New Graph (3 Steps)

### Step 1: Define State Type

```python
# browser_graph/graph_types/custom_state.py
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class CustomState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    custom_field: str  # Your custom field
```

### Step 2: Create Node

```python
# browser_graph/nodes/custom_node.py
def custom_node(state: CustomState) -> CustomState:
    # Your logic
    return {"custom_field": "new_value"}
```

### Step 3: Assemble Graph

```python
# browser_graph/graph/custom_graph.py
from langgraph.graph import StateGraph, END

def create_custom_graph():
    workflow = StateGraph(CustomState)
    
    workflow.add_node("custom", custom_node)
    workflow.set_entry_point("custom")
    workflow.add_edge("custom", END)
    
    return workflow.compile()
```

## Debugging Tips

### 1. View LLM Raw Output

Shown in logs:
```
LLM raw response: {"tool_name": "add", ...}
```

### 2. JSON Parsing Failed

Check if output contains valid JSON:
```python
logger.error(f"Raw content: {content}")
```

### 3. Tool Not Found

Ensure tool name matches exactly:
```python
# Check in all_tools
print([t.name for t in all_tools])
```

## Documentation Navigation

| Document | Audience | Content |
|----------|----------|---------|
| **QUICKSTART.md** (this) | Beginners | 5-minute quick start |
| **README.md** | Developers | Complete usage guide |
| **ARCHITECTURE.md** | Architects | Design and workflow |
| **CLASS_DESIGN.md** | In-depth | Implementation details |

## Next Steps

1. ✅ Run example to understand basic workflow
2. 📖 Read [ARCHITECTURE.md](ARCHITECTURE.md) to learn architecture
3. 🔧 Try adding a new tool
4. 🚀 Build your own application

## Need Help?

- Check log output
- Read [CLASS_DESIGN.md](CLASS_DESIGN.md)
- Verify API Key in `.env` file
- Ensure virtual environment is activated

---

**Enjoy!** 🎉

