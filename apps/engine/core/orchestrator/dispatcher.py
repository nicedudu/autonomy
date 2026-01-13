"""
能力分发器 (Capability Dispatcher)

职责：实现跨领域的原子能力派发。
集成 CommunicationBus 消息总线，实现执行状态的实时发布与外部审计。
"""

import logging
from typing import Any, Dict, Optional
from core.tools.registry import tool_registry
from core.agent.registry import agent_registry
from core.agent.agent import Agent
from core.session.session import Session
from core.orchestrator.schema import TaskResult
from core.communication_bus import bus

logger = logging.getLogger(__name__)

class CapabilityDispatcher:
    """
    全域任务调度器。
    """

    def __init__(self):
        # 持有通信总线引用，供 API 层进行回调绑定
        self.bus = bus

    async def dispatch(self, node_id: str, capability: str, arguments: Dict[str, Any], session: Session) -> TaskResult:
        """
        根据能力标识符执行派发逻辑。
        """
        # 发布起始事件到总线
        await self.bus.publish("task_started", {"node_id": node_id, "capability": capability, "session_id": session.id})

        # 1. 路径 A: 路由至原子工具
        tool_obj = tool_registry.get_tool(capability)
        if tool_obj:
            res = await tool_obj.execute(tool_params=arguments, session=session)
            result = TaskResult(
                node_id=node_id,
                status=res.status,
                output=res.output,
                error=res.error
            )
            # 发布结果事件
            await self.bus.publish("task_completed", result.model_dump())
            return result

        # 2. 路径 B: 路由至智能体 (递归委派)
        profile = agent_registry.get_profile(capability)
        if profile:
            from core.session.manager import session_manager
            sub_session = session_manager.create_session(parent_id=session.id)
            
            instruction = str(arguments.get("instruction", str(arguments)))
            
            from core.agent.executor import AgentExecutor
            sub_agent = Agent.create(profile, sub_session)
            executor = AgentExecutor()
            
            final_conclusion = ""
            try:
                async for event in executor.run(sub_agent, input_text=instruction):
                    if event["type"] == "conclusion":
                        final_conclusion = event["content"]
                    elif event["type"] == "error":
                        return TaskResult(node_id=node_id, status="error", error=event["content"])
                
                result = TaskResult(
                    node_id=node_id,
                    status="success",
                    output=final_conclusion or "子任务已完成。"
                )
                await self.bus.publish("task_completed", result.model_dump())
                return result
            except Exception as e:
                return TaskResult(node_id=node_id, status="error", error=str(e))

        # 3. 路径 C: 寻址失败
        error_res = TaskResult(
            node_id=node_id,
            status="error",
            error=f"能力路由失败: '{capability}' 未定义。"
        )
        await self.bus.publish("task_failed", error_res.model_dump())
        return error_res

# 全局派发单例
dispatcher = CapabilityDispatcher()