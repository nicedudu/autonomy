from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ProtocolTag(str, Enum):
    """
    系统标准 XML 协议标签。
    定义模型输出的结构化边界。
    """
    THOUGHT = "thought"       # 内部推理链 (Chain of Thought)
    PLAN = "plan"             # 动态任务清单
    ACTION = "action"         # 工具执行请求 (Function Calling)
    CALL = "call"             # 子智能体委派 (A2A Handoff)
    REFLECTION = "reflection" # 执行后的自我反思
    ARTIFACT = "artifact"     # 产生的长文本或代码块 (剥离对话流)
    CONCLUSION = "conclusion" # 最终任务结论

class ProtocolAction(BaseModel):
    """单条工具执行契约"""
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)

class ProtocolCall(BaseModel):
    """单条智能体协作契约"""
    target_id: str
    task: str
    context: Dict[str, Any] = Field(default_factory=dict)

class ProtocolResponse(BaseModel):
    """
    解析后的协议响应对象。
    """
    thought: Optional[str] = None
    plan: List[Dict[str, Any]] = Field(default_factory=list)
    actions: List[ProtocolAction] = Field(default_factory=list)
    calls: List[ProtocolCall] = Field(default_factory=list)
    reflection: Optional[str] = None
    conclusion: Optional[str] = None
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)
