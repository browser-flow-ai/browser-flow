from langgraph.constants import START, END
from langgraph.graph import StateGraph

from browser_common.browser_logging import get_logger
from browser_flow.flow_types.sh_graph_state import SHState
from browser_flow.graphs.base import BaseGraph
from browser_flow.nodes.conditional_node import ConditionalNode
from browser_flow.nodes.counter_node import CounterNode
from browser_flow.nodes.executor_node import ExecutorNode
from browser_flow.nodes.plan_node import PlanNode

logger = get_logger("browser_flow.graphs.base_graph", enable_file_logging=False)

class SHGraph(BaseGraph):
    def __init__(self, **kwargs):
        self._plan_node = PlanNode()
        self._conditional_node = ConditionalNode()
        self._executor_node = ExecutorNode()
        self._counter_node = CounterNode()

    @property
    def name(self):
        return "SH_Graph"

    @property
    def description(self):
        return "A Standard Graph with StageHand support"

    def build(self) -> StateGraph:
        workflow = StateGraph(SHState)

        workflow.add_node(self._plan_node.name, self._plan_node.execute)
        workflow.add_node(self._executor_node.name, self._executor_node.execute)
        workflow.add_node(self._conditional_node.name, self._conditional_node.execute)
        workflow.add_node(self._counter_node.name, self._counter_node.execute)

        # Add edges
        workflow.add_edge(START, self._plan_node.name)
        workflow.add_edge(self._plan_node.name, self._executor_node.name)
        workflow.add_edge(self._executor_node.name, self._conditional_node.name)
        workflow.add_edge(self._counter_node.name, END)

        # Conditional edge from conditional node
        # Branch from conditional: if done then END, otherwise back to executor
        def should_continue(state: SHState) -> str:
            done = getattr(state, "done", False)
            step_count = getattr(state, "step_count", 0)
            max_steps = getattr(state, "max_steps", 10)

            # Add state transition logging
            if done:
                return "COUNT"
            else:
                return "EXECUTOR"

        workflow.add_conditional_edges(
            self._conditional_node.name,
            should_continue,
            {
                "COUNT": self._counter_node.name,
                "EXECUTOR": self._executor_node.name,
            }
        )
        return workflow

def build_graph(session_id: str):
    logger.info("Building SH graph session_id: {}".format(session_id))
    graph = SHGraph()
    return graph.compile()
