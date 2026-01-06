import asyncio
import json
from typing import AsyncGenerator, Dict, Any, List, Optional
from core.agent.factory import AgentFactory
from core.agent.state import AgentStatus, MessageRole, AgentState
from core.communication_bus import CommunicationBus

class Orchestrator:
    """
    任务编排中枢。
    实现基于 Handoff 协议的多智能体协作。
    """
    def __init__(self):
        self.bus = CommunicationBus()

    async def dispatch(
        self,
        entry_agent_id: str,
        objective: str,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        分发根任务并管理协作生命周期。
        """
        # 创建根运行时
        runtime = AgentFactory.create_runtime(entry_agent_id)

        # 启动主协作循环
        async for event in self._execute_recursive(runtime, objective, context=initial_context):
            yield event

    async def _execute_recursive(
        self,
        runtime: Any,
        input_text: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        state: Optional[AgentState] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        处理单个 Agent 的生命周期并拦截 A2A 请求。
        """
        current_state = state
        current_input = input_text

        while True:
            handoff_requested = False

            # 运行当前 Agent 的推理循环
            async for step in runtime.run(current_input, existing_state=current_state, context=context):

                # 捕获 A2A 移交请求
                if step["type"] == "delegation_event":
                    payload = step["payload"]
                    target_id = payload["target_id"]
                    task_instruction = payload["task"]
                    sub_context = payload.get("context", {})

                    yield {"type": "event", "content": f"Handoff: @{runtime.agent.agent_id} -> @{target_id}"}

                    try:
                        # 1. 实例化目标专家智能体
                        sub_runtime = AgentFactory.create_runtime(target_id)

                        # 2. 递归执行子任务
                        sub_final_output = ""
                        async for sub_step in self._execute_recursive(sub_runtime, task_instruction, context=sub_context):
                            if sub_step["type"] == "stream":
                                sub_final_output += sub_step["content"]
                            yield sub_step

                        observation = f"<observation tool='delegate_to_{target_id}'>\nExpert @{target_id} finished. Summary:\n{sub_final_output}\n</observation>"

                    except ValueError as ve:
                        # 捕获智能体不存在的错误
                        observation = f"<observation status='error' tool='delegate_to_{target_id}'>\nError: Agent '{target_id}' not found. Please verify the Team Roster and only delegate to existing IDs.\n</observation>"
                    except Exception as e:
                        observation = f"<observation status='error' tool='delegate_to_{target_id}'>\nRuntime error during delegation: {str(e)}\n</observation>"

                    # 更新父 Agent 的状态并恢复执行
                    if runtime.state:
                        runtime.state.add_message(MessageRole.TOOL, observation, tool_call_id=step["tool_call_id"])
                        runtime.state.status = AgentStatus.THINKING

                    # 准备恢复父 Agent 循环
                    current_state = runtime.state
                    current_input = None # 不再需要用户输入，直接从 state 恢复
                    handoff_requested = True
                    break # 跳出当前运行，外层 while 会重新进入

                # 透传非 A2A 事件 (stream, conclusion, etc.)
                yield step

            # 如果推理正常结束且没有移交请求，则彻底退出本 Agent 的生命周期
            if not handoff_requested:
                break