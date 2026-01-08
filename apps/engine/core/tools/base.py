from typing import Any, Callable, Dict, Optional, TypeVar, cast
import functools
from pydantic import BaseModel

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
    name: str,
    description: str,
    parameters: Dict[str, Any]
) -> Callable[[F], F]:
    """
    生产级工具装饰器。
    
    将异步/同步函数封装为统一的 BaseTool 实例，并挂载元数据。
    """
    def decorator(func: F) -> F:
        # 创建工具实例
        instance = BaseTool(
            name=name,
            description=description,
            parameters=parameters,
            func=func
        )
        # 将实例挂载到原函数上，方便注册中心扫描提取
        setattr(func, "__tool__", instance)
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await instance.execute(*args, **kwargs)
            
        return cast(F, wrapper)
    return decorator