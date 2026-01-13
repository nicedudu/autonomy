"""
V4.0 编排协议模型 (Orchestration Protocol Schema)
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from core.schema.orchestration import WorkflowManifest, DispatchItem

class ProtocolReflection(BaseModel):
    trigger: str
    analysis: str
    correction: str

class ProtocolResponse(BaseModel):
    """
    V4.0 协议响应实体。
    支持记录解析错误，以驱动模型的自我修复循环。
    """
    raw_payload: str
    thought: Optional[str] = None
    blueprint: Optional[WorkflowManifest] = None
    dispatch: List[DispatchItem] = Field(default_factory=list)
    interaction: Optional[str] = None
    conclusion: Optional[str] = None
    reflection: Optional[ProtocolReflection] = None
    
    # 【核心增强】：记录解析过程中的异常，用于闭环重试
    errors: List[str] = Field(default_factory=list)
