from datetime import datetime
from typing import Any, Callable

from core.agent.state import AgentState
from core.middleware.base import BaseMiddleware


class EnvironmentMiddleware(BaseMiddleware):
    """
    环境注入中间件。
    负责在推理前观察环境（时间、工作目录等）并注入到 State。
    """

    async def __call__(self, state: AgentState, next_call: Callable) -> Any:
        # 1. 前置逻辑：注入环境信息
        state.context["current_time"] = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S")

        # 2. 步入下一层
        return await next_call(state)
