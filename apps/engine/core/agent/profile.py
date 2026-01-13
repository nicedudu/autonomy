"""
智能体规格定义 (Agent Profile Specification)

本模块定义了智能体的静态配置契约。
AgentProfile 是智能体的逻辑蓝图，包含了角色标识、职责声明、能力授权及推理配置。
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class AgentProfile(BaseModel):
    """
    智能体规格模型。
    """
    agent_id: str = Field(..., description="智能体唯一业务标识符。")
    name: str = Field(..., description="智能体的显示名称。")
    role_description: str = Field(..., description="智能体的核心职责与角色定位描述。")
    
    # 算力控制参数
    inference_params: Dict[str, Any] = Field(
        default_factory=lambda: {"temperature": 0.4, "max_tokens": 4096},
        description="模型推理采样参数。"
    )
    
    # 能力控制
    capability_mask: List[str] = Field(
        default_factory=list, 
        description="授权调用的原子工具或下游智能体标识列表。"
    )
    
    # 执行控制
    max_turns: int = Field(15, description="推理轮次配额。")
    middlewares: List[str] = Field(default_factory=list, description="该智能体需激活的特定中间件标识列表。")
    template_id: str = Field(..., description="关联的提示词指令模板标识。")
    
    metadata: Dict[str, Any] = Field(default_factory=dict, description="扩展元数据存储空间。")