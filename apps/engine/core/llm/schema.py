from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field

class LLMRole(str, Enum):
    """模型推理角色枚举。"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

class LLMMessage(BaseModel):
    """模型通信消息模型。"""
    role: LLMRole
    content: str
    name: Optional[str] = None

class LLMUsage(BaseModel):
    """推理资源消耗模型。"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class LLMResponse(BaseModel):
    """模型标准化响应模型。"""
    content: str
    model: str
    usage: LLMUsage
    finish_reason: Optional[str] = None
    raw: Any = Field(default=None, exclude=True)