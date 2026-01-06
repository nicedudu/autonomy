from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
import time

class AgentStatus(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    AWAITING_DELEGATION = "awaiting_delegation"
    COMPLETED = "completed"
    FAILED = "failed"

class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

class AgentMessage(BaseModel):
    role: MessageRole
    content: str
    tool_call_id: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class StateUpdate(BaseModel):
    """
    状态增量更新对象。
    由中间件或运行时产出，描述对 AgentState 的修改。
    """
    status: Optional[AgentStatus] = None
    context_updates: Dict[str, Any] = Field(default_factory=dict)
    new_messages: List[AgentMessage] = Field(default_factory=list)
    new_artifacts: Dict[str, Any] = Field(default_factory=dict)
    usage_delta: Dict[str, int] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AgentState(BaseModel):
    """
    智能体运行时状态 (唯一事实源)。
    遵循不可变原则：状态变更通过 Reducer 产生的 Update 合并。
    """
    agent_id: str
    session_id: str
    status: AgentStatus = AgentStatus.IDLE
    
    # 核心对话流 (压缩后的，不包含原始长数据)
    history: List[AgentMessage] = Field(default_factory=list)
    
    # 侧边缓冲区：存储超长数据块 (Artifacts)
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    
    # 全局共享上下文变量
    context: Dict[str, Any] = Field(default_factory=dict)
    
    # 资源消耗统计
    usage: Dict[str, int] = Field(default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0, "tool_calls": 0})
    
    # 系统元数据 (Internal only)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_message(self, role: MessageRole, content: str, **kwargs) -> AgentMessage:
        msg = AgentMessage(role=role, content=content, **kwargs)
        self.history.append(msg)
        return msg

    def update_context(self, updates: Dict[str, Any]):
        """合并 Context 更新"""
        self.context.update(updates)

    def apply_update(self, update: StateUpdate):
        """
        Reducer: 将增量更新合并到当前状态。
        """
        if update.status:
            self.status = update.status
        
        # 合并上下文变量
        self.context.update(update.context_updates)
        
        # 合并元数据
        self.metadata.update(update.metadata)
        
        # 处理特殊的 History 替换逻辑 (例如剪枝中间件建议的替换)
        if "new_history" in update.metadata:
            self.history = update.metadata["new_history"]
        
        # 追加新消息
        self.history.extend(update.new_messages)
        
        # 合并 Artifacts
        self.artifacts.update(update.new_artifacts)
        
        # 累加资源消耗
        for key, value in update.usage_delta.items():
            self.usage[key] = self.usage.get(key, 0) + value
