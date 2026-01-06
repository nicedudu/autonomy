from tools.web_search import web_search
from tools.web_fetch import web_fetch
from tools.planning import planning
from tools.python_executor import python_execute
from tools.file_ops import list_files, read_file, write_file
from tools.terminal import terminal_execute

# 核心工具原始列表 (被 @tool 装饰的函数)
CORE_TOOLS_RAW = [
    web_search,
    web_fetch,
    planning,
    python_execute,
    list_files,
    read_file,
    write_file,
    terminal_execute
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
