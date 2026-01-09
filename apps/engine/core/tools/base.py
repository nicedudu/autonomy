import functools
import inspect
from typing import Any, Callable, Dict, Optional, TypeVar, cast, get_type_hints
from pydantic import BaseModel, TypeAdapter

class ToolMetadata(BaseModel):
    """工具元数据模型"""
    name: str
    description: str
    parameters: Dict[str, Any]
    strict: bool = True

class ToolResult(BaseModel):
    """工具执行结果模型"""
    status: str  # "success" or "error"
    output: Any
    error: Optional[str] = None

class BaseTool:
    """
    智能体工具基类。
    所有具体工具需继承此类或通过装饰器转换。
    """

    def __init__(self, name: str, description: str, parameters: Dict[str, Any], func: Callable):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.func = func

    async def execute(self, **kwargs) -> ToolResult:
        """执行工具逻辑"""
        try:
            import asyncio
            if asyncio.iscoroutinefunction(self.func):
                res = await self.func(**kwargs)
            else:
                res = self.func(**kwargs)
            return ToolResult(status="success", output=res)
        except Exception as e:
            return ToolResult(status="error", output=None, error=str(e))

    def to_openai_format(self) -> Dict[str, Any]:
        """转换为 OpenAI 函数调用格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
                "strict": True
            }
        }

F = TypeVar("F", bound=Callable[..., Any])

def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None
) -> Callable[[F], F]:
    """
    生产级工具装饰器。
    
    支持自动推导 Schema 或显式定义。
    """
    def decorator(func: F) -> F:
        # 1. 自动推导元数据
        tool_name = name or func.__name__
        tool_desc = description or (inspect.getdoc(func) or "无描述").split("\n")[0]
        
        # 2. 自动构建参数 Schema (如果未显式提供)
        if parameters:
            params_schema = parameters
        else:
            sig = inspect.signature(func)
            try:
                hints = get_type_hints(func)
            except Exception:
                hints = {}

            properties = {}
            required = []
            for p_name, param in sig.parameters.items():
                if p_name in ("self", "cls", "session_id"): continue
                
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

        # 3. 创建工具实例
        instance = BaseTool(
            name=tool_name,
            description=tool_desc,
            parameters=params_schema,
            func=func
        )
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await instance.execute(*args, **kwargs)
            
        wrapper.__tool__ = instance
        return cast(F, wrapper)
    return decorator