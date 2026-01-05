from abc import ABC, abstractmethod
from typing import Any, Dict
from pydantic import BaseModel, Field

class BaseTool(ABC):
    """
    智能体工具基类。
    采用自描述架构，集成名称、描述及参数契约定义。
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """工具唯一标识名。"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具功能详述，供 LLM 推理参考。"""
        pass

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """符合 JSON Schema 标准的参数定义。"""
        pass

    @abstractmethod
    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """工具的物理执行逻辑。"""
        pass

    def to_schema(self) -> Dict[str, Any]:
        """将工具定义转换为 OpenAI 标准的 Tool Schema。"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
