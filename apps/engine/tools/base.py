import inspect
import functools
import re
from typing import Any, Dict, List, Callable, Optional, get_type_hints
from pydantic import TypeAdapter, BaseModel

class BaseTool:
    """
    智能体工具封装类 (MCP 风格)。
    利用 Pydantic TypeAdapter 自动化构建 100% 准确的 JSON Schema。
    """
    def __init__(self, func: Callable, name: str = None, description: str = None):
        self.func = func
        self._name = name or func.__name__
        
        # 1. 解析函数文档
        doc = inspect.getdoc(func) or ""
        self._description = description or (doc.split("\n")[0] if doc else "无描述")
        self._arg_docs = self._parse_docstring_args(doc)
        
        # 2. 自动化 Schema 构建
        self._parameters = self._build_parameters_schema()

    def _parse_docstring_args(self, doc: str) -> Dict[str, str]:
        """从 Docstring 中提取参数描述 (支持 Google/NumPy 风格)。"""
        arg_docs = {}
        # 匹配 "name: description" 格式
        pattern = re.compile(r"^\s*([\w_]+)\s*:\s*(.*)$\n", re.MULTILINE)
        for match in pattern.finditer(doc):
            arg_docs[match.group(1)] = match.group(2).strip()
        return arg_docs

    def _build_parameters_schema(self) -> Dict[str, Any]:
        """
        核心逻辑：利用 Pydantic TypeAdapter 生成 Schema。
        这能完美支持 Optional, Union, List, Dict 以及自定义 BaseModel。
        """
        sig = inspect.signature(self.func)
        hints = get_type_hints(self.func)
        
        properties = {}
        required = []
        
        for name, param in sig.parameters.items():
            if name == "self": continue
            
            # 获取类型注解，默认为 Any
            p_type = hints.get(name, Any)
            
            try:
                # 使用 Pydantic 的工业级转换器
                adapter = TypeAdapter(p_type)
                # 提取核心 Schema 结构
                schema = adapter.json_schema()
                
                # 注入从文档中提取的描述
                schema["description"] = self._arg_docs.get(name, f"参数 {name}")
                
                properties[name] = schema
                if param.default is inspect.Parameter.empty:
                    required.append(name)
            except Exception as e:
                # 极端情况下的回退逻辑
                properties[name] = {"type": "string", "description": str(e)}

        return {
            "type": "object",
            "properties": properties,
            "required": required
        }

    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具，适配同步与异步。"""
        if inspect.iscoroutinefunction(self.func):
            return await self.func(**params)
        return self.func(**params)

    def to_schema(self) -> Dict[str, Any]:
        """生成符合 OpenAI 工具调用规范的定义。"""
        return {
            "name": self._name,
            "description": self._description,
            "parameters": self._parameters
        }

def tool(name: str = None, description: str = None):
    """
    智能装饰器：将普通 Python 函数转化为 Agent 工具。
    """
    def decorator(func: Callable):
        # 包装函数
        t = BaseTool(func, name, description)
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
            
        # 挂载元数据，供注册中心发现
        wrapper.__tool__ = t
        return wrapper
    return decorator