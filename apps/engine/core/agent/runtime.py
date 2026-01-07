import asyncio
import uuid
import traceback
from typing import AsyncGenerator, Dict, Any, List, Optional, Callable

from core.agent.state import AgentState, AgentStatus, MessageRole, AgentMessage
from core.middleware.base import BaseMiddleware
from core.protocol.parser import ProtocolParser, ProtocolParseError
from core.prompt.compiler import prompt_compiler
from core.llm.manager import llm_manager
from core.llm.schema import LLMMessage, LLMRole
from core.schema.collaboration import ExecutionBlueprint
from core.tools.registry import tool_registry
from core.utils.logging import logger

class AgentRuntime:
    """分布式执行内核。"""

    def __init__(
        self,
        agent_id: str,
        provider_type: str,
        model: str,
        api_key: str,
        base_url: str,
        middlewares: Optional[List[BaseMiddleware]] = None,
        max_steps: int = 15
    ):
        self.agent_id = agent_id
        self.max_steps = max_steps
        self.middlewares = middlewares or []
        self.parser = ProtocolParser()
        self.llm_client = llm_manager.create_client(
            provider_type=provider_type,
            api_key=api_key,
            base_url=base_url,
            model=model
        )

    async def run(
        self,
        input_text: Optional[str] = None,
        blueprint: Optional[ExecutionBlueprint] = None,
        session_id: Optional[str] = None,
        existing_state: Optional[AgentState] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """驱动流式推理循环。"""
        self.state = existing_state or AgentState(
            agent_id=self.agent_id,
            session_id=session_id or str(uuid.uuid4())
        )
        
        if blueprint:
            self.state.metadata["active_blueprint"] = blueprint
            initial_prompt = blueprint.task.instruction
        else:
            initial_prompt = input_text

        if initial_prompt:
            self.state.add_message(MessageRole.USER, initial_prompt)

        self._prepare_authorized_tools()

        step_count = 0
        while step_count < self.max_steps:
            step_count += 1
            self.state.status = AgentStatus.THINKING

            try:
                # 1. 流式推理并即时 yield
                full_content = ""
                async for chunk in self._execute_inference_stream():
                    full_content += chunk
                    yield {"type": "stream", "content": chunk, "agent": self.agent_id}

                thought_msg = AgentMessage(role=MessageRole.ASSISTANT, content=full_content)
                self.state.history.append(thought_msg)

                # 2. 协议解析
                try:
                    proto_res = self.parser.parse(thought_msg.content)
                except ProtocolParseError as e:
                    error_obs = f"[协议解析失败] JSON 格式异常: {str(e)}"
                    self.state.add_message(MessageRole.TOOL, error_obs, name="protocol_fixer")
                    continue

                if proto_res.conclusion:
                    self.state.status = AgentStatus.COMPLETED
                    yield {"type": "conclusion", "content": proto_res.conclusion}
                    break

                if proto_res.calls:
                    self.state.status = AgentStatus.AWAITING_DELEGATION
                    from core.orchestrator.dispatcher import dispatcher
                    
                    # 核心重构：实时冒泡子任务的所有事件
                    async for sub_event in dispatcher.dispatch_calls(proto_res.calls, self.state.session_id):
                        if sub_event["type"] == "observation":
                            # 捕获聚合结果并回注状态机，终止本次冒泡
                            aggregation = sub_event["content"]
                            self.state.add_message(MessageRole.TOOL, aggregation, name="orchestrator_report")
                            yield sub_event
                        else:
                            # 透传子任务的过程事件 (stream, status 等)
                            yield sub_event
                    continue

                if proto_res.tool_calls:
                    self.state.status = AgentStatus.ACTING
                    for tool_call in proto_res.tool_calls:
                        # UI 反馈：注入状态气泡
                        yield {"type": "status", "content": f"正在运行工具: {tool_call.tool_name}", "agent": self.agent_id}
                        
                        res = await self._execute_tool_chain(tool_call.model_dump())
                        obs_content = self._format_observation(tool_call.tool_name, res)
                        
                        self.state.add_message(MessageRole.TOOL, obs_content, name=tool_call.tool_name)
                        yield {"type": "observation", "content": obs_content}

            except Exception as e:
                self.state.status = AgentStatus.FAILED
                logger.error(f"内核中断: {str(e)}", self.agent_id)
                yield {"type": "error", "content": str(e)}
                break

    async def _execute_inference_stream(self) -> AsyncGenerator[str, None]:
        """执行流式推理。"""
        from core.registry.internal import get_agent_definition
        definition = get_agent_definition(self.agent_id)

        async def core_stream(current_state: AgentState) -> AsyncGenerator[str, None]:
            blueprint = current_state.metadata.get("active_blueprint")
            system_prompt = prompt_compiler.compile_blueprint(blueprint, current_state) if blueprint else \
                            prompt_compiler.compile_agent_prompt(definition, current_state)
            messages = [LLMMessage(role=LLMRole(m.role.value), content=m.content) for m in current_state.history]
            async for chunk in self.llm_client.stream(messages=messages, system=system_prompt):
                yield chunk

        async for chunk in core_stream(self.state):
            yield chunk

    async def _execute_tool_chain(self, action: Dict[str, Any]) -> Any:
        """驱动工具执行洋葱链。"""
        async def core_tool(s: AgentState, act: Dict[str, Any]):
            tool_name = act.get("tool_name") or act.get("function")
            blueprint = s.metadata.get("active_blueprint")
            if blueprint and blueprint.resource.capability_mask and tool_name not in blueprint.resource.capability_mask:
                return {"status": "error", "message": f"权限拒绝: {tool_name}"}
            tool = tool_registry.get_tool(tool_name)
            if not tool: return {"status": "error", "message": f"工具未注册: {tool_name}"}
            return await tool.execute(**act.get("arguments", {}))

        chain = core_tool
        for mw in reversed(self.middlewares):
            def create_tool_wrapper(m, n): return lambda s, a: m.on_tool(s, a, n)
            chain = create_tool_wrapper(mw, chain)
        return await chain(self.state, action)

    def _prepare_authorized_tools(self):
        """装配授权工具文档。"""
        import json
        blueprint = self.state.metadata.get("active_blueprint")
        mask = blueprint.resource.capability_mask if blueprint else []
        docs = []
        for name, tool in tool_registry._tools.items():
            if not mask or name in mask:
                docs.append({"name": tool.name, "description": tool.description, "parameters": tool.parameters})
        
        docs.append({
            "name": "read_artifact",
            "description": "从共享内存中检索指定的产物内容。",
            "parameters": {"type": "object", "properties": {"artifact_id": {"type": "string"}}}
        })
        self.state.context["authorized_tools"] = json.dumps(docs, ensure_ascii=False)

    def _format_observation(self, tool_name: str, result: Any) -> str:
        """封装标准观测文本。"""
        import json
        from pydantic import BaseModel
        if isinstance(result, BaseModel):
            data = result.model_dump()
        else:
            data = result
        return json.dumps(data, ensure_ascii=False)