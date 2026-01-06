from core.tools.base import BaseTool, ToolMetadata, ToolResult
from core.tools.registry import tool_registry
import inspect
import functools
from typing import Any, Dict, List, Callable, Optional, get_type_hints
from pydantic import TypeAdapter

# 为了保持装饰器兼容性，重新实现 tool 装饰器逻辑，但产出符合 core 标准的实例
def tool(name: Optional[str] = None, description: Optional[str] = None):
    """
    工具定义装饰器。
    将普通函数转换为 core.tools.base.BaseTool 实例。
    """
    def decorator(func: Callable):
        # 1. 自动推导名称和描述
        tool_name = name or func.__name__
        tool_desc = description or (inspect.getdoc(func) or "无描述").split("\n")[0]
        
        # 2. 自动构建参数 Schema
        sig = inspect.signature(func)
        try:
            hints = get_type_hints(func)
        except Exception:
            hints = {}

        properties = {}
        required = []
        for p_name, param in sig.parameters.items():
            if p_name in ("self", "cls"): continue
            
            type_hint = hints.get(p_name, Any)
            try:
                adapter = TypeAdapter(type_hint)
                schema = adapter.json_schema()
                schema.pop("title", None)
                properties[p_name] = schema
            except Exception:
                properties[p_name] = {"type": "string"}
            
            if param.default is inspect.Parameter.empty:
                required.append(p_name)

        params_schema = {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False
        }

        # 3. 创建符合 V2 标准的实例
        instance = BaseTool(
            name=tool_name,
            description=tool_desc,
            parameters=params_schema,
            func=func
        )
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
            
        wrapper.__tool__ = instance
        return wrapper
    return decorator
