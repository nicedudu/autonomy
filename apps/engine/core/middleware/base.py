from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from core.agent.state import AgentState, StateUpdate, AgentMessage

class BaseMiddleware(ABC):
    """
    智能体中间件基类 (生命周期拦截器)。
    """

    async def pre_inference(self, state: AgentState) -> Optional[StateUpdate]:
        """
        在编译 System Prompt 和发送给 LLM 之前触发。
        用于动态注入上下文变量或拦截请求。
        """
        return None

    async def post_inference(self, state: AgentState, raw_response: str) -> Optional[StateUpdate]:
        """
        在 LLM 推理完成后触发。
        用于执行上下文清理、Token 统计或结果审计。
        """
        return None

    async def on_action(self, state: AgentState, action: Dict[str, Any], result: Any) -> Optional[StateUpdate]:
        """
        在工具执行完成后触发。
        """
        return None