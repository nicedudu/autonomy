from abc import ABC
from typing import Any, Callable, Dict

from core.agent.state import AgentState


class BaseMiddleware(ABC):
    """
    智能体通用洋葱模型中间件。

    支持推理链 (Inference) 与 工具链 (Action) 的双重拦截。
    """

    async def __call__(
        self,
        state: AgentState,
        next_call: Callable
    ) -> Any:
        """推理链执行入口 (由 Runtime 在推理前后驱动)"""
        return await next_call(state)

    async def on_tool(
        self,
        state: AgentState,
        action: Dict[str, Any],
        next_call: Callable
    ) -> Any:
        """工具链执行入口 (由 Runtime 在工具执行前后驱动)"""
        return await next_call(state, action)
