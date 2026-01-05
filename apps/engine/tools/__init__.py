from tools.web_search import web_search
from tools.web_fetch import WebFetchTool # 逐步重构中，暂时保留类
from tools.planning import PlanningTool
from tools.researcher import ResearcherTool

# 核心工具实例列表
# 支持函数包装对象和类实例
CORE_TOOLS_RAW = [
    web_search,
    WebFetchTool(),
    PlanningTool(),
    ResearcherTool()
]

# 标准化为 BaseTool 对象
CORE_TOOLS = []
for item in CORE_TOOLS_RAW:
    if hasattr(item, "__tool__"):
        CORE_TOOLS.append(item.__tool__)
    else:
        CORE_TOOLS.append(item)

def get_core_tool_schemas():
    """动态生成所有工具的 JSON Schema。"""
    return [t.to_schema() for t in CORE_TOOLS]
