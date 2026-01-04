from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

class Status(str, Enum):
    """通用执行状态枚举。"""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    RUNNING = "running"

class AgentInterface(BaseModel):
    """定义智能体的交互协议。"""
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)

class AgentManifest(BaseModel):
    """智能体声明式清单模型。"""
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
    """
    OpenAI Codex 标准技能清单模型。
    参考：https://developers.openai.com/codex/skills
    """
    name: str
    description: str
    metadata: Dict[str, Any] = Field(default_factory=dict) # 存储额外的非标准元数据
    instructions: Optional[str] = None # 对应 SKILL.md 的 Markdown 正文

class CollaborationCall(BaseModel):
    """智能体间协作调用的数据载体。"""
    target_id: str
    task: str
    context: Dict[str, Any] = Field(default_factory=dict)

class ActionCall(BaseModel):
    """内部工具调用的请求载体。"""
    tool_name: str
    params: Dict[str, Any] = Field(default_factory=dict)

class ActionResult(BaseModel):
    """工具执行结果回传模型。"""
    status: Status
    output: Any = None
    error: Optional[str] = None
    tool_name: Optional[str] = None

class Message(BaseModel):
    """系统总线通信消息模型。"""
    sender: str
    recipient: str
    subject: str
    content: Dict[str, Any]
    timestamp: float = Field(default_factory=lambda: __import__('time').time())
    message_type: str = "private"
