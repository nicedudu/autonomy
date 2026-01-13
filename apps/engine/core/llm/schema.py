"""
LLM 抽象契约协议 (LLM Abstract Protocol)
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

class LLMRole(str, Enum):
    """模型交互角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

class ToolCall(BaseModel):
    """工具调用意图载荷"""
    id: str = Field(..., description="调用唯一标识符")
    name: str = Field(..., description="目标函数/工具名称")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="解析后的参数负载")

class LLMProviderConfig(BaseModel):
    """算力供应商配置载荷"""
    provider_type: str = Field(..., description="供应商标识")
    model: str = Field(..., description="具体模型标识符")
    api_key: str = Field(..., description="访问凭证")
    base_url: Optional[str] = Field(None, description="API 终端地址")
    extra_options: Dict[str, Any] = Field(default_factory=dict, description="额外透传配置")

class LLMMessage(BaseModel):
    """标准化消息模型"""
    role: LLMRole
    content: Union[str, List[Dict[str, Any]]]
    name: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None

class LLMUsage(BaseModel):
    """成本审计模型"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class InferenceConfig(BaseModel):
    """
    推理采样配置。
    补全 top_p 等核心参数以对齐 Provider 实现。
    """
    temperature: float = Field(0.7, ge=0, le=2.0)
    top_p: float = Field(1.0, ge=0, le=1.0)
    max_tokens: Optional[int] = None
    stop: Optional[List[str]] = None
    extra_params: Dict[str, Any] = Field(default_factory=dict)

class LLMResponse(BaseModel):
    """标准化响应"""
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    model: str
    usage: LLMUsage
    raw: Any = None
