from typing import Dict, Any, List
from abc import ABC, abstractmethod

class BaseTool(ABC):
    """
    所有工具的基础类。
    设计参考 MCP (Model Context Protocol) 标准，
    以便未来能无缝接入标准化的 Agent 编排工具。
    """
    
    def __init__(self, tool_name: str, description: str, input_schema: Dict[str, Any] = None):
        self.tool_name = tool_name
        self.description = description
        self.input_schema = input_schema or {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    @abstractmethod
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具功能"""
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """获取工具信息，用于生成 LLM 的 Tool Definition"""
        return {
            "name": self.tool_name,
            "description": self.description,
            "parameters": self.input_schema
        }
