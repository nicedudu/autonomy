"""
基础消息数据模型 (Core Message Schema)

本模块定义了系统中最底层的通信契约。
它不依赖任何核心组件，仅作为跨领域的通用数据结构存在，用于彻底解决循环依赖。
"""

import time
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class MessageRole(str, Enum):
    """通信角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

class AgentMessage(BaseModel):
    """
    通用消息实体。
    """
    role: MessageRole
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[Any]] = None # 存储意图
    timestamp: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)