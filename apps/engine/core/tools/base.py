import functools
import inspect
import logging
from typing import Any, Callable, Dict, Optional, TypeVar, cast, get_type_hints, Union
from pydantic import BaseModel, create_model, Field

logger = logging.getLogger(__name__)

class ToolResult(BaseModel):
    """
    原子工具执行结果封装。
    用于标准化不同业务逻辑的输出载荷。
    """
    status: str
    output: Any
    error: Optional[str] = None

class BaseTool(BaseModel):
    """
    工具实体抽象。
    管理工具的契约解析（Schema Generation）与运行时的 Session 注入。
    """
    name: str
    description: str
    parameters: Dict[str, Any]
    func: Callable = Field(exclude=True)

    class Config:
        arbitrary_types_allowed = True

    async def execute(self, tool_params: Dict[str, Any], session: Any) -> ToolResult:
        """
        触发工具执行。
        
        采用签名内省机制实现 Session 实例的直接注入。
        注入逻辑：
        1. 遍历函数签名参数。
        2. 若参数名为 'session'，则注入当前会话实体。
        3. 否则从模型提供的业务负载 (tool_params) 中按名匹配。
        """
        try:
            sig = inspect.signature(self.func)
            final_kwargs = {}
            
            for param_name in sig.parameters:
                # 注入点：直接注入 Session 对象
                if param_name == "session":
                    final_kwargs[param_name] = session
                
                # 业务参数填充
                elif param_name in tool_params:
                    final_kwargs[param_name] = tool_params[param_name]

            # 逻辑执行
            if inspect.iscoroutinefunction(self.func):
                res = await self.func(**final_kwargs)
            else:
                res = self.func(**final_kwargs)
                
            return ToolResult(status="success", output=res)
            
        except Exception as e:
            logger.error(f"Execution Error [{self.name}]: {e}", exc_info=True)
            return ToolResult(status="error", output=None, error=str(e))

    def to_openai_format(self) -> Dict[str, Any]:
        """导出 OpenAI 兼容的 Function Calling 契约"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }

F = TypeVar("F", bound=Callable[..., Any])

def tool(
    _func: Optional[F] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> Union[F, Callable[[F], F]]:
    """
    工具自举装饰器。
    
    实现“定义与执行分离”：
    1. 自动解析函数签名，生成业务级 JSON Schema。
    2. 自动屏蔽 'session' 注入参数，确保模型契约纯净。
    """
    def decorator(func: F) -> F:
        tool_name = name or func.__name__
        docstring = inspect.getdoc(func) or ""
        tool_desc = description or (docstring.split("\n")[0] if docstring else "Undefined")

        sig = inspect.signature(func)
        type_hints = get_type_hints(func)
        fields = {}
        
        # 核心逻辑：凡是名为 session 的参数均视为系统注入项，不在契约中体现
        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls", "session"):
                continue
            
            annotation = type_hints.get(param_name, Any)
            default = param.default if param.default is not inspect.Parameter.empty else ...
            fields[param_name] = (annotation, default)

        # 构建契约验证模型
        DynamicModel = create_model(f"{tool_name}Args", **fields)
        try:
            schema = DynamicModel.model_json_schema()
        except AttributeError:
            schema = DynamicModel.schema()

        if "title" in schema:
            del schema["title"]

        tool_instance = BaseTool(
            name=tool_name,
            description=tool_desc,
            parameters=schema,
            func=func
        )

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            session = kwargs.pop("session", None)
            return await tool_instance.execute(kwargs, session=session)
            
        setattr(wrapper, "__tool__", tool_instance)
        return cast(F, wrapper)

    if _func is None: return decorator
    return decorator(_func)
