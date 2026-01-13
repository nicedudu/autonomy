"""
智能体状态枚举 (Agent State Enums)
"""

from enum import Enum

class AgentStatus(str, Enum):
    """智能体运行状态"""
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    AWAITING_DELEGATION = "awaiting_delegation"
    COMPLETED = "completed"
    FAILED = "failed"