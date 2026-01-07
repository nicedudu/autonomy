from typing import Any, Callable

from core.agent.state import AgentState
from core.middleware.base import BaseMiddleware


class ContextManagerMiddleware(BaseMiddleware):
    """
    上下文生命周期管理器。
    负责在推理前根据上下文窗口限制自动“修剪”历史记录。
    """

    def __init__(self, max_history_len: int = 15):
        self.max_history_len = max_history_len

    async def __call__(self, state: AgentState, next_call: Callable) -> Any:
        """
        洋葱模型执行逻辑。
        """
        # 1. 前置逻辑：修剪历史
        if len(state.history) > self.max_history_len:
            pruned_history = state.history[-self.max_history_len:]
            print(
                f"\033[94m[ContextManager] Pruning history: {len(state.history)} -> {len(pruned_history)}\033[0m")
            # 在洋葱模型中，我们可以直接操作 state (虽然建议使用 apply_update)
            # 但为了确立权限，我们暂时直接修改，之后可优化为更严谨的 Reducer 模式
            state.history = pruned_history
            state.context["history_pruned"] = True

        # 2. 步入下一层
        return await next_call(state)
