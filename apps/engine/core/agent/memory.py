import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class Artifact(BaseModel):
    """共享产物实体。"""
    id: str = Field(default_factory=lambda: f"art_{uuid.uuid4().hex[:8]}")
    content: Any
    type: str
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MemoryGateway:
    """系统级内存网关。
    
    管理执行节点间的共享内存空间，支持基于会话的产物脱水与复水。
    """

    def __init__(self):
        self._storage: Dict[str, Dict[str, Artifact]] = {}

    def store(self, session_id: str, content: Any, art_type: str = "text", metadata: Optional[Dict[str, Any]] = None) -> str:
        """持久化产物并返回引用标识。
        
        Args:
            session_id: 会话 ID。
            content: 原始数据。
            art_type: 业务分类。
            metadata: 描述元数据。
            
        Returns:
            str: 产物唯一索引标识。
        """
        if session_id not in self._storage:
            self._storage[session_id] = {}
        
        artifact = Artifact(content=content, type=art_type, metadata=metadata or {})
        self._storage[session_id][artifact.id] = artifact
        return artifact.id

    def retrieve(self, session_id: str, artifact_id: str) -> Optional[Artifact]:
        """根据 ID 检索产物实体。"""
        return self._storage.get(session_id, {}).get(artifact_id)

    def hydrate(self, session_id: str, artifact_refs: List[str]) -> str:
        """执行上下文复水逻辑。
        
        Args:
            session_id: 会话 ID。
            artifact_refs: 引用 ID 列表。
            
        Returns:
            str: 拼接后的上下文文本。
        """
        segments = []
        for ref_id in artifact_refs:
            art = self.retrieve(session_id, ref_id)
            if art:
                segments.append(f"--- Artifact: {ref_id} ({art.type}) ---\n{str(art.content)}")
        return "\n\n".join(segments)

    def clear_session(self, session_id: str):
        """释放指定会话内存。"""
        self._storage.pop(session_id, None)

memory_gateway = MemoryGateway()