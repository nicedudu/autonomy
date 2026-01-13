"""
会话生命周期管理器 (Session Lifecycle Manager)
"""

from typing import Dict, List, Optional
from core.session.session import Session

class SessionManager:
    """
    负责会话的创建与状态检索。
    """

    def __init__(self):
        self._sessions: Dict[str, Session] = {}

    def create_session(self, user_id: Optional[str] = None, parent_id: Optional[str] = None) -> Session:
        """
        初始化一个会话。
        """
        if parent_id and parent_id in self._sessions:
            parent = self._sessions[parent_id]
            new_session = parent.create_child()
        else:
            new_session = Session.create_root(user_id=user_id)
            
        self._sessions[new_session.id] = new_session
        return new_session

    def get_session(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)

    def list_active_sessions(self) -> List[str]:
        """
        列出当前活跃的会话标识。
        """
        return list(self._sessions.keys())

    def destroy_session(self, session_id: str):
        self._sessions.pop(session_id, None)

# 全局单例
session_manager = SessionManager()
