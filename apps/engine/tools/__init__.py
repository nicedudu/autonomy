from tools.web_search import WebSearchTool
from tools.web_fetch import WebFetchTool
from tools.planning import PlanningTool
from tools.researcher import ResearcherTool

# 全局核心工具集
# AgentRuntime 会通过此列表动态生成 System Prompt 中的工具文档
CORE_TOOLS = [
    WebSearchTool(),
    WebFetchTool(),
    PlanningTool(),
    ResearcherTool()
]

def get_core_tool_schemas():
    """获取所有核心工具的 JSON Schema 定义。"""
    return [t.to_schema() for t in CORE_TOOLS]