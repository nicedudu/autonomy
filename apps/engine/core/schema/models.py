from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

class Status(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    RUNNING = "running"

class AgentInterface(BaseModel):
    """Defines the interaction contract for an agent."""
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)

class AgentManifest(BaseModel):
    """Declarative manifest for an agent."""
    agent_id: str
    name: str
    role: str
    description: Optional[str] = None
    interface: AgentInterface = Field(default_factory=AgentInterface)
    capabilities: List[str] = Field(default_factory=list)
    model: Optional[str] = None
    provider_id: Optional[str] = None
    system_prompt_template: Optional[str] = None

class SkillManifest(BaseModel):
    """技能声明式清单"""
    skill_id: str
    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    implementation: str
    required_permissions: List[str] = Field(default_factory=list)

class CollaborationCall(BaseModel):
    """跨智能体协作请求载体"""
    target_id: str
    task: str
    context: Dict[str, Any] = Field(default_factory=dict)

class ActionCall(BaseModel):
    """内部工具调用载体"""
    tool_name: str
    params: Dict[str, Any] = Field(default_factory=dict)

class ActionResult(BaseModel):
    """工具执行结果回传"""
    status: Status
    output: Any = None
    error: Optional[str] = None
    tool_name: Optional[str] = None

class Message(BaseModel):
    """智能体间通信消息模型"""
    sender: str
    recipient: str
    subject: str
    content: Dict[str, Any]
    timestamp: float = Field(default_factory=lambda: __import__('time').time())
    message_type: str = "private"
