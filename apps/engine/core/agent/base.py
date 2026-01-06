from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncGenerator
from core.agent.state import AgentState, AgentMessage
from core.schema.models import AgentManifest

class BaseAgent(ABC):
    """
    智能体抽象基类。
    定义了 Agent 的核心属性和与 LLM 交互的基本接口。
    """

    def __init__(self, manifest: AgentManifest):
        self.manifest = manifest
        self.agent_id = manifest.agent_id
        self.name = manifest.name
        self.role = manifest.role

    @abstractmethod
    async def think(self, state: AgentState) -> AgentMessage:
        """
        推理环节：根据当前状态，决定下一步行动。
        实现类需在此调用 LLM。
        """
        pass

    @abstractmethod
    def get_system_prompt(self, state: AgentState) -> str:
        """
        构建系统提示词。
        支持从 manifest 或动态上下文生成。
        """
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.name} id={self.agent_id}>"
