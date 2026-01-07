"""
协议数据契约 (Protocol Schema)

定义执行引擎解析后的标准化组件模型。
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ProtocolAction(BaseModel):
    """工具调用组件：映射至行业标准 tool_calls 结构。"""
    tool_name: str = Field(..., alias="function") # 兼容习惯，也支持 tool_name
    arguments: Dict[str, Any] = Field(default_factory=dict)

class ProtocolCall(BaseModel):
    """协作委派组件：定义跨节点任务。"""
    id: str = Field(..., description="任务唯一标识符")
    agent_id: str = Field(..., description="目标执行单元 ID")
    instruction: str = Field(..., description="子任务指令")
    artifact_refs: List[str] = Field(default_factory=list)
    mode: str = Field(default="sync")

class ProtocolResponse(BaseModel):
    """全量协议载荷：模型产出的结构化指令块。"""
    thought: Optional[str] = None
    tool_calls: List[ProtocolAction] = Field(default_factory=list)
    calls: List[ProtocolCall] = Field(default_factory=list)
    conclusion: Optional[str] = None
