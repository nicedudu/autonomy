"""
系统级内存网关 (System Memory Gateway)

职责：管理智能体会话内的隔离产物（Artifacts）。
严格遵循 Session 独立原则，确保每个执行单元仅能访问授权给当前会话的物理内存空间。
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

class Artifact(BaseModel):
    """共享产物实体"""
    id: str = Field(..., description="产物唯一标识符")
    content: Any = Field(..., description="产物载荷数据")
    type: str = Field("text", description="数据类型")
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MemoryGateway:
    """
    内存网关控制中心。
    """

    def __init__(self):
        # 存储模型回归：{session_id: {artifact_id: Artifact}}
        self._storage: Dict[str, Dict[str, Artifact]] = {}

    def store(self, session_id: str, artifact: Artifact):
        """
        将产物存入当前会话的隔离空间。
        """
        if session_id not in self._storage:
            self._storage[session_id] = {}
        
        self._storage[session_id][artifact.id] = artifact
        return artifact.id

    def retrieve(self, session_id: str, artifact_id: str) -> Optional[Artifact]:
        """
        仅限当前会话内的检索。
        """
        return self._storage.get(session_id, {}).get(artifact_id)

    def clear_session(self, session_id: str):
        """
        销毁会话关联的内存。
        """
        self._storage.pop(session_id, None)

# 全局单例
memory_gateway = MemoryGateway()