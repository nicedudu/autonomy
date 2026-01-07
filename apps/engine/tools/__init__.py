from tools.web_search import web_search
from tools.web_fetch import web_fetch
from tools.planning import planning
from tools.file_ops import list_files, read_file, write_file
from core.tools.system_tools import read_artifact_tool

# 核心工具原始列表 (已移除高危的 python_execute 和 terminal_execute)
CORE_TOOLS_RAW = [
    web_search,
    web_fetch,
    planning,
    list_files,
    read_file,
    write_file,
    read_artifact_tool
]

# 标准化提取 BaseTool 对象
CORE_TOOLS = []
for item in CORE_TOOLS_RAW:
    if hasattr(item, "__tool__"):
        CORE_TOOLS.append(item.__tool__)
    else:
        CORE_TOOLS.append(item)

def get_core_tool_schemas():
    """生成所有核心工具的 OpenAI 兼容定义格式。"""
    return [t.to_dict() for t in CORE_TOOLS]