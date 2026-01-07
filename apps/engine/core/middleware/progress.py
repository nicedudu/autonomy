"""
执行进度中间件 (UI Progress Middleware)

负责实时截获执行节点的工具调用状态，并将其封装为进度事件发布至通信总线。
支持前端看板实现对分布式任务执行节点的颗粒度监控。
"""

from typing import Any, Callable, Dict
from core.middleware.base import BaseMiddleware
from core.agent.state import AgentState
from core.communication_bus import bus # 假设全局总线单例

class UIProgressMiddleware(BaseMiddleware):
    """
    进度冒泡拦截器。
    
    在工具执行的前后发布状态事件，实现执行过程的透明化。
    """

    async def on_tool(self, state: AgentState, action: Dict[str, Any], next_call: Callable) -> Any:
        tool_name = action.get("tool_name", "unknown")
        
        # 1. 发布“正在执行”事件
        await bus.publish("progress_event", {
            "session_id": state.session_id,
            "agent_id": state.agent_id,
            "status": "acting",
            "detail": f"正在运行工具: {tool_name}"
        })

        try:
            # 2. 执行核心工具逻辑
            result = await next_call(state, action)
            
            # 3. 发布“执行完成”事件
            await bus.publish("progress_event", {
                "session_id": state.session_id,
                "agent_id": state.agent_id,
                "status": "completed",
                "detail": f"工具 {tool_name} 执行完毕"
            })
            
            return result
            
        except Exception as e:
            # 4. 异常冒泡
            await bus.publish("progress_event", {
                "session_id": state.session_id,
                "agent_id": state.agent_id,
                "status": "error",
                "detail": f"工具执行异常: {str(e)}"
            })
            raise e
