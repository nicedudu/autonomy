"""
基础日志中间件 (Logging Middleware)

拦截推理链与工具链的生命周期，提供自动化的耗时统计、参数审计及异常堆栈记录。
"""

import time
import json
from typing import Any, Callable, Dict
from core.middleware.base import BaseMiddleware
from core.agent.state import AgentState
from core.utils.logging import logger

class LoggingMiddleware(BaseMiddleware):
    """
    运行时审计拦截器。
    
    采用洋葱模型实现对执行节点的全景观测。
    """

    async def __call__(self, state: AgentState, next_call: Callable) -> Any:
        """推理链审计"""
        logger.info(f"==> 推理开始: {state.agent_id}", state.agent_id)
        start_time = time.time()

        try:
            response = await next_call(state)
            duration = time.time() - start_time
            logger.success(f"<== 推理结束 | 耗时: {duration:.2f}s", state.agent_id)
            return response
        except Exception as e:
            logger.error(f"推理异常: {str(e)}", state.agent_id)
            raise e

    async def on_tool(self, state: AgentState, action: Dict[str, Any], next_call: Callable) -> Any:
        """工具链审计"""
        tool_name = action.get("tool_name") or action.get("function") or "unknown"
        logger.debug(f"工具调用 [{tool_name}] | 参数: {json.dumps(action.get('arguments', {}), ensure_ascii=False)}", state.agent_id)
        
        start_time = time.time()
        try:
            result = await next_call(state, action)
            duration = time.time() - start_time
            logger.success(f"工具返回 [{tool_name}] | 耗时: {duration:.2f}s", state.agent_id)
            return result
        except Exception as e:
            logger.error(f"工具崩溃 [{tool_name}]: {str(e)}", state.agent_id)
            raise e