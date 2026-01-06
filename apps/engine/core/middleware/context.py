from typing import Optional, Dict, Any
from core.middleware.base import BaseMiddleware
from core.agent.state import AgentState, StateUpdate

class ContextManagerMiddleware(BaseMiddleware):
    """
    上下文生命周期管理器。
    负责在推理前根据上下文窗口限制自动“修剪”历史记录。
    """

    def __init__(self, max_history_len: int = 15):
        self.max_history_len = max_history_len

    async def pre_inference(self, state: AgentState) -> Optional[StateUpdate]:
        """
        推理前检查历史深度。
        """
        if len(state.history) <= self.max_history_len:
            return None

        # 执行剪枝逻辑：保留最近的 N 条，并标记状态已被修剪
        # 注意：通常保留 SYSTEM 消息不被修剪，但这里我们的 history 中只有 USER/ASSISTANT/TOOL
        pruned_history = state.history[-self.max_history_len:]
        
        print(f"\033[94m[ContextManager] Pruning history: {len(state.history)} -> {len(pruned_history)}\033[0m")

        return StateUpdate(
            context_updates={"history_pruned": True},
            # 在这里我们返回一个全量覆盖的建议，或者特定的更新标识
            # 目前我们的 AgentState.history 是 List，Reducer 模式下我们建议替换它
            metadata={"new_history": pruned_history} 
        )
