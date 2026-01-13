"""
原子工具箱全量定义 (Autonomy Toolbelt Registry)

按领域模型整合并导出所有受控原子工具。
本模块负责将工具函数与全局注册表（ToolRegistry）进行绑定。
"""

from core.tools.registry import tool_registry

# 1. 导入各领域重构后的工具集
from tools.workspace import list_workspace_files, read_workspace_file, write_workspace_file
from tools.internet import search_internet, fetch_web_page
from tools.kernel import get_artifact_content
from tools.task import manage_task_steps

# 2. 声明生产环境核心工具集 (Manifest)
PRODUCTION_TOOLS = [
    # 工作空间管理
    list_workspace_files,
    read_workspace_file,
    write_workspace_file,
    
    # 互联网能力
    search_internet,
    fetch_web_page,
    
    # 内核支撑
    get_artifact_content,
    
    # 任务追踪
    manage_task_steps
]

# 3. 自动化注册至全局单例
for tool_func in PRODUCTION_TOOLS:
    tool_registry.register(tool_func)

def get_registered_tool_schemas():
    """
    导出所有已注册工具的 OpenAI 兼容 JSON Schema。
    """
    return tool_registry.get_schemas()

# 导出符号，确保 API 或 Runtime 层可直接调用
__all__ = [
    "list_workspace_files",
    "read_workspace_file",
    "write_workspace_file",
    "search_internet",
    "fetch_web_page",
    "get_artifact_content",
    "manage_task_steps",
    "get_registered_tool_schemas"
]
