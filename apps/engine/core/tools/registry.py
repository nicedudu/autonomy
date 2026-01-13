from typing import Dict, List, Optional, Union, Callable
from core.tools.base import BaseTool

class ToolRegistry:
    """
    工具注册中心。
    负责维护全局可调用的原子工具实例，提供元数据检索与执行体路由功能。
    """

    def __init__(self):
        # 存储映射：ToolName -> BaseTool 实例
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool_obj: Union[BaseTool, Callable]):
        """
        注册工具至中心。
        支持 BaseTool 实例或经过 @tool 装饰的函数。
        """
        tool_instance = None
        
        # 解析装饰器注入的工具实例
        if hasattr(tool_obj, "__tool__"):
            tool_instance = getattr(tool_obj, "__tool__")
        elif isinstance(tool_obj, BaseTool):
            tool_instance = tool_obj
            
        if not tool_instance:
            raise ValueError(f"无效的注册对象: {tool_obj}。对象必须是 BaseTool 实例或经过 @tool 装饰的函数。")

        # 逻辑：覆盖注册，确保工具定义的实时更新
        self._tools[tool_instance.name] = tool_instance

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        检索指定名称的工具实例。
        """
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        """
        列出所有已注册的工具。
        """
        return list(self._tools.values())

    def get_schemas(self) -> List[Dict]:
        """
        导出所有工具的 OpenAI 标准函数契约。
        用于模型推理时的 context 填充。
        """
        return [t.to_openai_format() for t in self._tools.values()]


# 导出全局注册表单例
tool_registry = ToolRegistry()
