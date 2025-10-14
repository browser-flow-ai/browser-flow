# Architecture Design

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      User Input                              │
│                   (HumanMessage)                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │    Agent     │
                  │     Node     │
                  │ (LLM Decision)│
                  └──────┬───────┘
                         │
                  Condition Check
                         │
            ┌────────────┴────────────┐
            │                         │
            ▼                         ▼
     Need Tool Call?            No Tool Needed
            │                         │
            ▼                         ▼
     ┌──────────────┐            ┌─────────┐
     │    Tools     │            │   END   │
     │     Node     │            │  Finish │
     │ (Execute Tool)│           └─────────┘
     └──────┬───────┘
            │
            │ Return Result
            │
            ▼
     ┌──────────────┐
     │    Agent     │
     │     Node     │
     │(Process Result)│
     └──────────────┘
```

## Data Flow

### 1. State Flow

```python
GraphState = {
    "messages": [Message1, Message2, ...]
}
```

Each node receives current state, processes it, and returns state update.

### 2. DeepSeek Tool Calling Flow

**Important**: DeepSeek doesn't support `bind_tools()`. Need to guide LLM to return JSON-formatted tool call instructions via prompt.

**Example**: "Please calculate 15 + 27"

1. **Agent Node - First Call**:
   - Put tool descriptions in prompt
   - LLM returns JSON: 
   ```json
   {
     "tool_name": "add",
     "parameters": {"a": 15, "b": 27},
     "reasoning": "User needs to calculate sum of two numbers",
     "final_answer": null
   }
   ```
   - Parse using `PydanticOutputParser`
   - Generate AIMessage with tool_calls

2. **Tools Node**: 
   - Find tool named "add"
   - Execute: `add_numbers(15, 27)`
   - Return ToolMessage(content="42")

3. **Agent Node - Second Call**: 
   - Detect previous message is ToolMessage
   - Generate friendly answer based on tool result
   - Return AIMessage(content="The sum of 15 and 27 is 42")

### 3. Key Differences

| Method | OpenAI/Function Calling Support | DeepSeek |
|--------|----------------------------------|----------|
| Tool Binding | `llm.bind_tools(tools)` | ❌ Not supported |
| Tool Description | Automatic | ✅ Manual in prompt |
| Output Format | Native tool_calls | ✅ JSON + Parser |
| Tool Execution | ToolNode automatic | ✅ Manual find and invoke |

## Component Responsibilities

### graph_types/
- **Responsibility**: Define data structures and types
- **Features**: Use TypedDict and Pydantic
- **Examples**: GraphState, various config types

### handlers/
- **Responsibility**: Implement specific business logic
- **Features**: Pure functions, easy to test
- **Examples**: Calculator functions, data processing

### tools/
- **Responsibility**: Wrap handlers as LLM-callable tools
- **Features**: Use StructuredTool with parameter validation
- **Examples**: add_tool, multiply_tool

### nodes/
- **Responsibility**: Define processing nodes in graph
- **Features**: Receive GraphState, return state update
- **Examples**: agent_node, tool_node

### graph/
- **Responsibility**: Organize nodes to build complete workflow
- **Features**: Use StateGraph to define flow and edges
- **Examples**: simple_graph

## Extension Patterns

### Adding New Functionality Steps

1. **Define Processing Logic** (handlers/)
   ```python
   def search_web(query: str) -> str:
       # Implement search logic
       pass
   ```

2. **Wrap as Tool** (tools/)
   ```python
   search_tool = StructuredTool.from_function(
       func=search_web,
       name="search",
       description="Search web pages",
       args_schema=SearchInput,
   )
   ```

3. **Add to Tool List**
   ```python
   all_tools = [add_tool, multiply_tool, search_tool]
   ```

4. **(Optional) Create Dedicated Node** (nodes/)
   ```python
   def search_node(state: GraphState) -> GraphState:
       # Custom search node logic
       pass
   ```

5. **(Optional) Build New Graph** (graph/)
   ```python
   def create_search_graph():
       workflow = StateGraph(GraphState)
       # Add nodes and edges
       return workflow.compile()
   ```

## Best Practices

1. **Single Responsibility**: Each handler does one thing
2. **Type Safety**: Use Pydantic for input validation
3. **Logging**: Log at critical points
4. **Error Handling**: Handle exceptions in handlers
5. **Test Friendly**: Handlers are pure functions, easy to unit test

## System Advantages

### 1. Maintainability ✅

- Clear inheritance relationships
- Unified interface specifications
- Easy to understand and modify

### 2. Extensibility ✅

- New components just inherit base classes
- No impact on existing code
- Follows Open-Closed Principle

### 3. Testability ✅

- Single responsibility per class
- Dependency injection easy to mock
- Pure functions easy to test

### 4. Type Safety ✅

- Abstract methods enforce implementation
- IDE auto-completion and checking
- Reduce runtime errors

### 5. Team Collaboration ✅

- Unified development standards
- Clear code structure
- Lower learning curve

