import os

from browser_flow.flow_types.sh_graph_state import SHState
from browser_flow.nodes.base import BaseNode
from dotenv import load_dotenv

load_dotenv()

if os.getenv("DASHSCOPE_API_KEY"):
    from browser_common.llm.llm_qwen import llm
else:
    from browser_common.llm.llm_deepseek import llm

from browser_common.browser_logging import get_logger
logger = get_logger("browser_flow.counter_node", enable_file_logging=False)

class CounterNode(BaseNode[SHState]):
    def __init__(self, tools=None):
        self.tools = tools

    @property
    def name(self) -> str:
        return "COUNTER_NODE"

    async def execute(self, state: SHState) -> dict:
        print(state.issues)
        return {}