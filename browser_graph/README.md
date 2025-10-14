# Browser Graph - LangGraph Example

A minimal LangGraph example demonstrating how to organize and build a simple Agent application.

> 🚀 **Quick Start**: Check [QUICKSTART.md](QUICKSTART.md) to get started in 5 minutes!

## Features

- ✅ Support for **DeepSeek** LLM (tool calling via prompt engineering)
- ✅ Clean **modular architecture** (handlers → tools → nodes → graph)
- ✅ Complete **type definitions** and data validation
- ✅ Detailed **logging** and error handling
- ✅ **Ready-to-use** example code

## Directory Structure

```
browser_graph/
├── graph_types/              # Type definitions
│   ├── state.py             # Graph state type
│   └── output_schema.py     # LLM output schema
├── handlers/                 # Handlers (business logic)
│   ├── base.py              # BaseHandler base class ⭐
│   └── calculator.py        # Calculator handler
├── tools/                    # Tool wrappers (StructuredTool)
│   ├── base.py              # BaseTool base class ⭐
│   └── calculator_tools.py  # Calculator tools
├── utils/                    # Utility functions
│   └── tools_description.py # Generate tool descriptions
├── nodes/                    # Graph nodes
│   ├── base.py              # BaseNode base class ⭐
│   ├── agent_node.py        # Agent node
│   └── tool_node.py         # Tool node
├── graph/                    # Graph structures
│   ├── base.py              # BaseGraph base class ⭐
│   └── simple_graph.py      # Simple graph definition
├── examples/                 # Example code
│   ├── run_simple_graph.py  # Python example
│   └── run.sh               # Quick start script
├── README.md                 # Complete documentation
├── QUICKSTART.md             # Quick start guide ⭐
├── ARCHITECTURE.md           # Architecture design
└── CLASS_DESIGN.md           # Class design specification ⭐
```

## Component Overview

### 0. Base Class System ⭐ - Unified Standards

Each module directory has its own `base.py` base class to ensure components follow unified interfaces:

- **`handlers/base.py`** - `BaseHandler` - Base class for all handlers
- **`tools/base.py`** - `BaseTool` - Base class for all tools
- **`nodes/base.py`** - `BaseNode` - Base class for all nodes
- **`graph/base.py`** - `BaseGraph` - Base class for all graphs

See [CLASS_DESIGN.md](CLASS_DESIGN.md) for class design specifications.

### 1. graph_types/ - Type Definitions

Define graph state types using TypedDict and annotations.

```python
class GraphState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
```

### 2. handlers/ - Handlers

Implement actual business logic, such as calculations and data processing.

```python
def execute(self, a: int, b: int) -> int:
    return a + b
```

### 3. tools/ - Tool Wrappers

Wrap handlers as StructuredTools for LLM use.

```python
add_tool = StructuredTool.from_function(
    func=add_numbers,
    name="add",
    description="Add two numbers together",
    args_schema=AddInput,
)
```

**Note**: DeepSeek doesn't support `bind_tools()`. Instead, use `generate_tools_description()` to put tool descriptions in the prompt, and let the LLM return JSON-formatted tool call instructions.

### 4. nodes/ - Nodes

Define processing nodes in the graph.

- **agent_node**: Use LLM for decision-making (via tool descriptions in prompt)
- **tool_node**: Manually execute tool calls (find and invoke tools)

**Workflow**:
1. Agent node puts tool descriptions in prompt
2. LLM returns JSON output (with tool name and parameters)
3. Use `PydanticOutputParser` to parse JSON
4. Tool node finds and executes the corresponding tool
5. Return execution result to Agent node for final answer

### 5. graph/ - Graph Structures

Use StateGraph to organize nodes and edges, defining the workflow.

```python
workflow = StateGraph(GraphState)
workflow.add_node("agent", agent)
workflow.add_node("tools", tool_node)
workflow.add_conditional_edges("agent", should_continue, {...})
```

## Environment Setup

### Poetry Virtual Environment

```bash
source /Users/farmer/Library/Caches/pypoetry/virtualenvs/agentql-kwV3nYNt-py3.13/bin/activate
```

Or set Python interpreter path:
```
/Users/farmer/Library/Caches/pypoetry/virtualenvs/agentql-kwV3nYNt-py3.13/bin/python
```

### LLM Configuration

This example uses **DeepSeek** as the LLM via the `browser_common.llm.llm_deepseek` module.

API Key is configured in the project's `.env` file:
```bash
DEEPSEEK_API_KEY=your_api_key_here
```

The code automatically loads environment variables via `dotenv`, no manual setup needed.

## Run Example

### Method 1: Quick Start Script

```bash
./browser_graph/examples/run.sh
```

### Method 2: Manual Run

```bash
# Activate virtual environment
source /Users/farmer/Library/Caches/pypoetry/virtualenvs/agentql-kwV3nYNt-py3.13/bin/activate

# Run example
cd browser-flow
python -m browser_graph.examples.run_simple_graph
```

## Example Output

```
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

## Extending the System

### Adding a New Tool (3 steps)

1. In `handlers/` implement the business logic
2. In `tools/` wrap as StructuredTool
3. Add to the `all_tools` list

### Creating a New Graph (3 steps)

1. In `graph_types/` define the state
2. In `nodes/` create nodes
3. In `graph/` assemble the workflow

## Dependencies

- langgraph
- langchain-core
- langchain-community (DeepSeek)
- pydantic
- python-dotenv

All dependencies are configured in the project's Poetry environment.

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** ⭐ - 5-minute quick start
- **[CLASS_DESIGN.md](CLASS_DESIGN.md)** ⭐ - Class design specifications and best practices
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed architecture design and workflow

## FAQ

### Q: Why not use `bind_tools()`?
A: DeepSeek doesn't support OpenAI's Function Calling API. We need to use prompt engineering to make the LLM return JSON-formatted tool call instructions.

### Q: How to add a new tool?
A: 
1. Implement business logic in `handlers/`
2. Wrap as StructuredTool in `tools/`
3. Add to the `all_tools` list

### Q: How to debug LLM output?
A: The logging system automatically records LLM's raw output and parsing process. Check logs for "LLM raw response" and "Reasoning".

### Q: What if JSON parsing fails?
A: 
1. Check if LLM's raw output is valid JSON
2. Ensure prompt includes format instructions (`tool_call_parser.get_format_instructions()`)
3. Try adding more examples in the prompt

## Tech Stack

- **LangGraph**: Build complex Agent workflows
- **LangChain**: LLM abstraction layer
- **DeepSeek**: Large Language Model
- **Pydantic**: Data validation and schema definition
- **Poetry**: Python dependency management

