import inspect
import functools
import re
from typing import Any, Dict, List, Callable, Optional, get_type_hints
from pydantic import TypeAdapter

class BaseTool:
    """
    智能体工具封装。
    """
    def __init__(self, func: Callable, name: str = None, description: str = None):
        """初始化工具并生成契约。"""
        self.func = func
        self._name = name or func.__name__
        
        # 提取描述
        doc = inspect.getdoc(func) or ""
        self._description = description or (doc.split("\n")[0] if doc else "无描述")
        
        # 提取参数文档
        self._arg_docs = {}
        for line in doc.split("\n"):
            match = re.search(r"^\s*([\w_]+)\s*:\s*(.*)$", line)
            if match:
                self._arg_docs[match.group(1)] = match.group(2).strip()
        
        self._parameters = self._build_schema()

    def _build_schema(self) -> Dict[str, Any]:
        """构建兼容 LLM 的参数 Schema。"""
        sig = inspect.signature(self.func)
        try:
            hints = get_type_hints(self.func)
        except Exception:
            hints = {}

        properties = {}
        required = []
        
        for name, param in sig.parameters.items():
            if name in ("self", "cls"): continue
            
            type_hint = hints.get(name, Any)
            try:
                # 使用 TypeAdapter 生成 Schema 并精简
                schema = TypeAdapter(type_hint).json_schema()
                schema.pop("title", None) # 移除 Pydantic 默认标题
                schema["description"] = self._arg_docs.get(name, f"参数 {name}")
                properties[name] = schema
            except Exception:
                properties[name] = {"type": "string", "description": self._arg_docs.get(name, f"参数 {name}")}
            
            if param.default is inspect.Parameter.empty:
                required.append(name)
                
        return {"type": "object", "properties": properties, "required": required}

    async def run(self, **kwargs) -> Any:
        """安全执行工具逻辑。"""
        if inspect.iscoroutinefunction(self.func):
            return await self.func(**kwargs)
        return self.func(**kwargs)

    def to_schema(self) -> Dict[str, Any]:
        """返回 OpenAI 定义格式。"""
        return {
            "name": self._name,
            "description": self._description,
            "parameters": self._parameters
        }

def tool(name: str = None, description: str = None):
    """
    工具定义装饰器 (MCP 风格)。
    """
    def decorator(func: Callable):
        # 创建工具封装实例
        t = BaseTool(func, name, description)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
            
        # 挂载工具对象，供系统发现
        wrapper.__tool__ = t
        return wrapper
    return decorator