"""
会话实体模型 (Session Entity Model)

本模块定义了系统的核心执行载荷。
支持层级化会话（Session Tree），用于追踪递归智能体调用的血缘关系与状态隔离。
"""

import time
import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from core.schema.message import AgentMessage

class Session(BaseModel):
    """
    会话实例实体。
    
    承载单次任务的全量上下文。支持父子会话关联，实现多级递归调用的物理隔离。
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # --- 会话溯源 (Lineage) ---
    parent_id: Optional[str] = Field(None, description="父级会话标识符。")
    root_id: str = Field(..., description="根会话标识符，用于跨层级追踪。")
    
    user_id: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    
    # 核心历史
    history: List[AgentMessage] = Field(default_factory=list)
    
    # 状态元数据
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # 权限掩码
    capability_mask: List[str] = Field(default_factory=list)

    def add_message(self, message: AgentMessage):
        """记录交互历史。"""
        self.history.append(message)

    def update_metadata(self, key: str, value: Any):
        """更新会话状态数据。"""
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """检索会话状态数据。"""
        return self.metadata.get(key, default)

    @classmethod
    def create_root(cls, user_id: Optional[str] = None, session_id: Optional[str] = None) -> "Session":
        """
        工厂方法：创建根会话（任务树的起点）。
        """
        sid = session_id or str(uuid.uuid4())
        return cls(id=sid, root_id=sid, user_id=user_id)

    def create_child(self) -> "Session":
        """
        工厂方法：基于当前会话创建一个子会话（用于递归委派）。
        子会话继承 root_id 与 user_id，但拥有独立的 id 和 history。
        """
        return Session(
            parent_id=self.id,
            root_id=self.root_id,
            user_id=self.user_id,
            capability_mask=self.capability_mask # 继承父级能力边界
        )