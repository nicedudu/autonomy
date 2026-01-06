from typing import Dict, List, Optional
from core.tools.base import BaseTool

class ToolRegistry:
    """
    工具注册表。
    负责管理系统中所有可用的原子工具。
    """
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        """注册一个工具"""
        if tool.name in self._tools:
            # 允许覆盖，但输出警告或记录日志
            pass
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """根据名称获取工具"""
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        """列出所有已注册工具"""
        return list(self._tools.values())

    def get_schemas(self) -> List[Dict]:
        """获取所有工具的 OpenAI 格式 Schema"""
        return [t.to_openai_format() for t in self._tools.values()]

# 全局工具注册表实例
tool_registry = ToolRegistry()
