# Class Design Specification

This project uses **Object-Oriented** design. All core components (Handler, Tool, Node, Graph) are defined as classes, following unified standards and inheritance hierarchy.

## Design Principles

### 1. Based on Abstract Base Classes (ABC)

All components inherit from abstract base classes to ensure:
- ✅ **Unified Interface** - All similar components follow the same interface
- ✅ **Enforced Standards** - Must implement abstract methods
- ✅ **Type Safety** - Better type checking and IDE support
- ✅ **Easy Extension** - New components just inherit base classes

**Base Class Locations**:
- `BaseHandler` → `handlers/base.py`
- `BaseTool` → `tools/base.py`
- `BaseNode` → `nodes/base.py`
- `BaseGraph` → `graph/base.py`

Each base class is in its corresponding module directory, enhancing module cohesion and independence.

### 2. Single Responsibility Principle

Each class is responsible for one thing:
- **Handler** - Pure business logic
- **Tool** - Tool wrapping and parameter validation
- **Node** - Graph node execution logic
- **Graph** - Workflow organization and orchestration

### 3. Dependency Injection

Components inject dependencies through constructors:
```python
# Tool depends on Handler
class AddTool(BaseTool):
    def __init__(self):
        self._handler = AddHandler()

# Node depends on Tools
class AgentNode(BaseNode):
    def __init__(self, tools=None):
        self._tools = tools or []

# Graph depends on Nodes
class SimpleGraph(BaseGraph):
    def __init__(self):
        self._agent_node = AgentNode()
        self._tool_node = ToolNode()
```

---

## Four Base Classes

### 1. BaseHandler - Handler Base Class

**Location**: `handlers/base.py`

**Responsibility**: Implement specific business logic

```python
# browser_graph/handlers/base.py
class BaseHandler(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Handler name"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Handler description"""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Execute handler logic"""
        pass
```

**Must Implement**:
- `name` - Handler unique identifier
- `description` - Functionality description
- `execute(**kwargs)` - Execution logic

**Example**:
```python
# browser_graph/handlers/calculator.py
from browser_graph.handlers.base import BaseHandler

class AddHandler(BaseHandler):
    @property
    def name(self) -> str:
        return "add"
    
    @property
    def description(self) -> str:
        return "Add two numbers together"
    
    def execute(self, a: int, b: int) -> int:
        return a + b
```

**Standards**:
- ✅ Handler should be a pure function, side-effect free (except logging)
- ✅ Clear parameter types
- ✅ Clear return type
- ✅ Detailed docstrings

---

### 2. BaseTool - Tool Base Class

**Location**: `tools/base.py`

**Responsibility**: Wrap Handler as StructuredTool with parameter validation

```python
# browser_graph/tools/base.py
from browser_graph.handlers.base import BaseHandler

class BaseTool(ABC):
    @property
    @abstractmethod
    def handler(self) -> BaseHandler:
        """Associated handler"""
        pass
    
    @abstractmethod
    def to_structured_tool(self) -> StructuredTool:
        """Convert to StructuredTool"""
        pass
```

**Must Implement**:
- `handler` - Associated Handler instance
- `to_structured_tool()` - Convert to LangChain StructuredTool

**Example**:
```python
# browser_graph/tools/calculator_tools.py
from browser_graph.tools.base import BaseTool
from browser_graph.handlers.calculator import AddHandler

class AddTool(BaseTool):
    def __init__(self):
        self._handler = AddHandler()
    
    @property
    def handler(self) -> BaseHandler:
        return self._handler
    
    def to_structured_tool(self) -> StructuredTool:
        return StructuredTool.from_function(
            func=self._handler.execute,
            name=self._handler.name,
            description=self._handler.description,
            args_schema=AddInputSchema,  # Pydantic model
        )
```

**Standards**:
- ✅ Tool holds Handler instance
- ✅ Use Pydantic to define parameter schema
- ✅ Tool name and description inherited from Handler
- ✅ Export StructuredTool instance for use

---

### 3. BaseNode - Node Base Class

**Location**: `nodes/base.py`

**Responsibility**: Define processing nodes in the graph

```python
# browser_graph/nodes/base.py
from browser_graph.graph_types.state import GraphState

class BaseNode(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Node name"""
        pass
    
    @abstractmethod
    def execute(self, state: GraphState) -> GraphState:
        """Execute node logic"""
        pass
```

**Must Implement**:
- `name` - Node unique identifier
- `execute(state)` - Node execution logic

**Example**:
```python
# browser_graph/nodes/agent_node.py
from browser_graph.nodes.base import BaseNode

class AgentNode(BaseNode):
    def __init__(self, tools=None):
        self._tools = tools or all_tools
    
    @property
    def name(self) -> str:
        return "agent"
    
    def execute(self, state: GraphState) -> GraphState:
        # Process messages, call LLM, return state update
        messages = state["messages"]
        # ... processing logic
        return {"messages": [new_message]}
```

**Standards**:
- ✅ Node receives GraphState, returns state update
- ✅ Don't directly modify input state, return new update
- ✅ Can inject dependencies in constructor (e.g., tools)
- ✅ Keep node logic cohesive

---

### 4. BaseGraph - Graph Base Class

**Location**: `graph/base.py`

**Responsibility**: Organize nodes to build complete workflow

```python
# browser_graph/graph/base.py
from langgraph.graph import StateGraph

class BaseGraph(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Graph name"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Graph description"""
        pass
    
    @abstractmethod
    def build(self) -> StateGraph:
        """Build the graph"""
        pass
    
    def compile(self):
        """Compile the graph"""
        return self.build().compile()
```

**Must Implement**:
- `name` - Graph unique identifier
- `description` - Graph functionality description
- `build()` - Build StateGraph

**Example**:
```python
# browser_graph/graph/simple_graph.py
from browser_graph.graph.base import BaseGraph
from browser_graph.nodes.agent_node import AgentNode
from browser_graph.nodes.tool_node import ToolNode

class SimpleGraph(BaseGraph):
    def __init__(self):
        self._agent_node = AgentNode()
        self._tool_node = ToolNode()
    
    @property
    def name(self) -> str:
        return "simple_graph"
    
    @property
    def description(self) -> str:
        return "A simple Agent graph with tool calling support"
    
    def build(self) -> StateGraph:
        workflow = StateGraph(GraphState)
        
        # Add nodes
        workflow.add_node(self._agent_node.name, self._agent_node.execute)
        workflow.add_node(self._tool_node.name, self._tool_node.execute)
        
        # Set edges and conditions
        workflow.set_entry_point(self._agent_node.name)
        workflow.add_conditional_edges(...)
        workflow.add_edge(...)
        
        return workflow
```

**Standards**:
- ✅ Graph initializes required Nodes in constructor
- ✅ `build()` method assembles StateGraph
- ✅ Provide factory function for convenience: `create_xxx_graph()`
- ✅ Conditional logic can be defined as private methods

---

## Component Relationships

```
BaseHandler ──┐
              │
              ▼
           BaseTool ──┐
                      │
                      ▼
                  BaseNode ──┐
                             │
                             ▼
                         BaseGraph
```

**Dependency Chain**:
```
Handler → Tool → Node → Graph
```

---

## Usage Examples

### Create New Handler

```python
# browser_graph/handlers/search.py
from browser_graph.handlers.base import BaseHandler

class SearchHandler(BaseHandler):
    @property
    def name(self) -> str:
        return "search"
    
    @property
    def description(self) -> str:
        return "Search web content"
    
    def execute(self, query: str) -> str:
        # Implement search logic
        return f"Search results: {query}"
```

### Create Corresponding Tool

```python
# browser_graph/tools/search_tools.py
from browser_graph.tools.base import BaseTool
from browser_graph.handlers.search import SearchHandler

class SearchInputSchema(BaseModel):
    query: str = Field(description="Search query")

class SearchTool(BaseTool):
    def __init__(self):
        self._handler = SearchHandler()
    
    @property
    def handler(self) -> BaseHandler:
        return self._handler
    
    def to_structured_tool(self) -> StructuredTool:
        return StructuredTool.from_function(
            func=self._handler.execute,
            name=self._handler.name,
            description=self._handler.description,
            args_schema=SearchInputSchema,
        )
```

---

## Best Practices

### 1. Handler Design

```python
✅ Recommended
class AddHandler(BaseHandler):
    def execute(self, a: int, b: int) -> int:
        logger.info(f"Executing addition: {a} + {b}")
        return a + b

❌ Not Recommended
class AddHandler:  # No base class
    def add(self, a, b):  # Inconsistent method name
        return a + b  # No type annotations
```

### 2. Tool Design

```python
✅ Recommended
class AddTool(BaseTool):
    def __init__(self):
        self._handler = AddHandler()  # Compose Handler
    
    def to_structured_tool(self) -> StructuredTool:
        return StructuredTool.from_function(
            func=self._handler.execute,  # Use Handler method
            name=self._handler.name,
            description=self._handler.description,
            args_schema=AddInputSchema,  # Pydantic validation
        )

❌ Not Recommended
def add_tool():  # Using function instead of class
    return StructuredTool.from_function(
        func=lambda a, b: a + b,  # Logic directly written
        name="add",
        description="add",
    )
```

---

## Summary

By using **classes** to define all components, we achieve:

1. **Unified Standards** - All components follow the same interface
2. **Clear Responsibilities** - Each class does one thing
3. **Easy Extension** - Inherit base class to add new features
4. **Type Safety** - Better type checking and IDE support
5. **Easy Testing** - Dependency injection and single responsibility
6. **Team Collaboration** - Unified code style and structure

This design makes the project have **stronger maintainability** and **extensibility**! 🎯

