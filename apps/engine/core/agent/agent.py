"""
智能体实体模型 (Agent Entity Model)

本模块定义了智能体的运行时实例。
Agent 类作为核心聚合根，将静态的 AgentProfile 与运行时的 Session 边界进行物理绑定。
"""

from typing import TYPE_CHECKING
from core.agent.profile import AgentProfile

if TYPE_CHECKING:
    from core.session.session import Session

class Agent:
    """
    智能体运行时实例。
    
    代表了一个具备特定规格并在隔离环境下工作的执行主体。
    """

    def __init__(self, profile: AgentProfile, session: 'Session'):
        """
        初始化智能体实例。
        """
        self.profile = profile
        self.session = session
        
        # 运行时属性
        self.agent_id = profile.agent_id
        self.name = profile.name

    def __repr__(self) -> str:
        return f"<Agent(id={self.agent_id}, session={self.session.id})>"

    @classmethod
    def create(cls, profile: AgentProfile, session: 'Session') -> "Agent":
        """
        工厂方法：实例化智能体。
        """
        return cls(profile, session)