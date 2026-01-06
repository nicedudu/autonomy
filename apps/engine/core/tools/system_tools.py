from typing import Dict, Any
from core.tools.base import BaseTool, ToolResult
from core.schema.collaboration import DelegationRequest
import json

async def delegate_to_agent_func(target_agent_id: str, instruction: str, **kwargs) -> Dict[str, Any]:
    """
    将任务委派给另一个专家智能体。
    
    target_agent_id: 目标智能体的 ID (如 'researcher', 'coder')
    instruction: 明确的任务指令
    """
    # 这个函数在 Runtime 中被调用时，其实际效果是返回一个带有特殊标识的 Dict
    # Runtime 会检测这个标识并将其转化为 A2A 调用
    return {
        "__type__": "delegation_call",
        "target_agent_id": target_agent_id,
        "instruction": instruction,
        "context": kwargs
    }

# 实例化工具对象
delegate_tool = BaseTool(
    name="delegate_to_agent",
    description="Delegate a sub-task to a specialist agent when you need expert help.",
    parameters={
        "type": "object",
        "properties": {
            "target_agent_id": {"type": "string", "description": "The ID of the specialist agent."},
            "instruction": {"type": "string", "description": "Clear and detailed task instructions for the agent."}
        },
        "required": ["target_agent_id", "instruction"]
    },
    func=delegate_to_agent_func
)
