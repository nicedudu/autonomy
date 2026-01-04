from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from core.schema.models import ActionCall, ActionResult

class AgentMiddleware(ABC):
    """
    智能体运行时中间件基类。
    允许在 Agent 生命周期的关键节点注入逻辑。
    """

    async def on_startup(self, agent_id: str, prompt: str) -> None:
        """Agent 启动时触发"""
        pass

    async def on_before_think(self, agent_id: str, history: List[Dict]) -> Optional[List[Dict]]:
        """
        LLM 思考前触发。
        允许中间件读取甚至修改传入 LLM 的消息历史 (Context)。
        如果返回 List[Dict]，则后续流程将使用该新的历史记录；
        如果返回 None，则使用原始记录。
        """
        pass

    async def on_after_think(self, agent_id: str, response: str) -> str:
        """LLM 思考后触发 (可用于记录日志或修改响应)"""
        return response

    async def on_before_action(self, agent_id: str, action: ActionCall) -> None:
        """工具执行前触发"""
        pass

    async def on_after_action(self, agent_id: str, action: ActionCall, result: ActionResult) -> None:
        """工具执行后触发"""
        pass

    async def on_shutdown(self, agent_id: str) -> None:
        """Agent 结束时触发"""
        pass
