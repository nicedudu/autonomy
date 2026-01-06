from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field

class DelegationRequest(BaseModel):
    """发起委托请求"""
    source_agent_id: str
    target_agent_id: str
    instruction: str              # 给目标 Agent 的具体指令
    context: Dict[str, Any] = Field(default_factory=dict)
    sync: bool = True             # 是否同步等待结果

class DelegationResult(BaseModel):
    """委托执行结果"""
    status: Literal["success", "failure"]
    output: str                   # 文本总结
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
