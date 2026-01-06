from datetime import datetime
from typing import Optional, Dict, Any
from core.middleware.base import BaseMiddleware
from core.agent.state import AgentState, StateUpdate

class EnvironmentMiddleware(BaseMiddleware):
    """
    环境注入中间件。
    负责在推理前观察环境（时间、工作目录等）并注入到 State。
    """

    async def pre_inference(self, state: AgentState) -> Optional[StateUpdate]:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 注入到 metadata，由 PromptCompiler 读取
        return StateUpdate(
            context_updates={
                "current_time": now
            }
        )
