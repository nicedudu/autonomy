"""
分布式协议执行内核 (V3.5 Specification)

职责：驱动执行单元的标准化生命周期。
核心机制：
1. 采用洋葱模型拦截全链路事件。
2. 强制执行“复水-推理-分发-脱水”的确定性状态机流转。
3. 实现系统上下文与工具参数的自动、精准注入。
"""

import asyncio
import uuid
import inspect
from typing import AsyncGenerator, Dict, Any, List, Optional, Callable, TYPE_CHECKING

from core.agent.state import AgentState, AgentStatus, MessageRole, AgentMessage
from core.middleware.base import BaseMiddleware
from core.protocol.parser import ProtocolParser, ProtocolParseError
from core.prompt.compiler import prompt_compiler
from core.llm.manager import llm_manager
from core.llm.schema import LLMMessage, LLMRole
from core.tools.registry import tool_registry
from core.utils.logging import logger

if TYPE_CHECKING:
    from core.schema.collaboration import ExecutionBlueprint

class AgentRuntime:
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
        self.model_label = model
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
        blueprint: Optional['ExecutionBlueprint'] = None,
        session_id: Optional[str] = None,
        existing_state: Optional[AgentState] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """[顶层设计] 执行单元标准化生命周期循环。"""
        # 1. 状态复水 (Hydration)
        self.state = existing_state or AgentState(
            agent_id=self.agent_id,
            session_id=session_id or str(uuid.uuid4())
        )
        if blueprint:
            self.state.metadata["active_blueprint"] = blueprint
            if blueprint.task.instruction:
                self.state.add_message(MessageRole.USER, blueprint.task.instruction)
        elif input_text:
            self.state.add_message(MessageRole.USER, input_text)

        # 2. 环境预装配 (Sandbox Preparation)
        self._prepare_authorized_tools()

        step_count = 0
        while step_count < self.max_steps:
            step_count += 1
            self.state.status = AgentStatus.THINKING

            try:
                # A. 推理阶段：编译指令并驱动流式推理
                system_prompt = await self._compile_prompt()
                
                full_content = ""
                # 构造符合 LLM 契约的消息序列
                current_messages = [LLMMessage(role=LLMRole(m.role.value), content=m.content) for m in self.state.history]
                
                async for chunk in self.llm_client.stream(messages=current_messages, system=system_prompt):
                    full_content += chunk
                    yield {"type": "stream", "content": chunk, "agent": self.agent_id}

                # B. 审计阶段：全量 Trace 记录
                logger.trace(self.agent_id, self.model_label, system_prompt, [m.model_dump() for m in current_messages], full_content)
                
                thought_msg = AgentMessage(role=MessageRole.ASSISTANT, content=full_content)
                self.state.history.append(thought_msg)

                # C. 解析阶段：指令载荷反序列化
                try:
                    proto_res = self.parser.parse(full_content)
                except ProtocolParseError as e:
                    error_obs = f"[协议解析失败] 指令块格式异常: {str(e)}。请修正 JSON 结构。"
                    self.state.add_message(MessageRole.TOOL, error_obs, name="protocol_parser")
                    continue

                # D. 分发与执行阶段 (Fan-out)
                if proto_res.conclusion:
                    self.state.status = AgentStatus.COMPLETED
                    yield {"type": "conclusion", "content": proto_res.conclusion}
                    break

                if proto_res.calls:
                    # 递归任务委派逻辑
                    async for event in self._handle_delegations(proto_res.calls):
                        yield event
                    continue

                if proto_res.tool_calls:
                    # 本地工具调用逻辑
                    async for event in self._handle_actions(proto_res.tool_calls):
                        yield event

            except Exception as e:
                self.state.status = AgentStatus.FAILED
                logger.error(f"生命周期崩溃: {str(e)}", self.agent_id)
                yield {"type": "error", "content": str(e)}
                break

    async def _compile_prompt(self) -> str:
        """[核心机制] 触发中间件并编译提示词。"""
        # 触发洋葱中间件
        async def noop_next(s): pass
        for mw in self.middlewares:
            await mw(self.state, noop_next)
            
        from core.registry.internal import get_agent_definition
        definition = get_agent_definition(self.agent_id)
        blueprint = self.state.metadata.get("active_blueprint")
        
        if blueprint:
            return prompt_compiler.compile_blueprint(blueprint, self.state)
        return prompt_compiler.compile_agent_prompt(definition, self.state)

    async def _handle_delegations(self, calls: List[Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """处理 A2A 任务委派。"""
        from core.orchestrator.dispatcher import dispatcher
        self.state.status = AgentStatus.AWAITING_DELEGATION
        
        async for sub_event in dispatcher.dispatch_calls(calls, self.state.session_id):
            if sub_event["type"] == "observation":
                self.state.add_message(MessageRole.TOOL, sub_event["content"], name="orchestrator_report")
                yield sub_event
            else:
                yield sub_event

    async def _handle_actions(self, actions: List[Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """处理原子工具动作。"""
        self.state.status = AgentStatus.ACTING
        for act in actions:
            yield {"type": "status", "content": f"正在运行: {act.tool_name}", "agent": self.agent_id}
            
            # 精准参数注入
            args = act.arguments
            tool = tool_registry.get_tool(act.tool_name)
            if tool:
                sig = inspect.signature(tool.func)
                if "session_id" in sig.parameters:
                    args["session_id"] = self.state.session_id
            
            res = await self._execute_tool_chain({"tool_name": act.tool_name, "arguments": args})
            obs_content = self._format_observation(act.tool_name, res)
            self.state.add_message(MessageRole.TOOL, obs_content, name=act.tool_name)
            yield {"type": "observation", "content": obs_content}

    async def _execute_tool_chain(self, action: Dict[str, Any]) -> Any:
        """驱动工具拦截链。"""
        async def core_tool(s: AgentState, act: Dict[str, Any]):
            tool = tool_registry.get_tool(act.get("tool_name"))
            if not tool: return {"status": "error", "message": f"未注册: {act.get('tool_name')}"}
            return await tool.execute(**act.get("arguments", {}))

        chain = core_tool
        for mw in reversed(self.middlewares):
            def create_tool_wrapper(m, n): return lambda s, a: m.on_tool(s, a, n)
            chain = create_tool_wrapper(mw, chain)
        return await chain(self.state, action)

    def _prepare_authorized_tools(self):
        """[权限规格化] 装配能力掩码。"""
        import json
        blueprint = self.state.metadata.get("active_blueprint")
        mask = blueprint.resource.capability_mask if blueprint else []
        docs = []
        for name, tool in tool_registry._tools.items():
            if not mask or name in mask:
                docs.append({"name": tool.name, "description": tool.description, "parameters": tool.parameters})
        
        # 始终注入系统级产物读取契约
        docs.append({
            "name": "read_artifact",
            "description": "从共享内存中检索指定的产物内容。参数: artifact_id",
            "parameters": {"type": "object", "properties": {"artifact_id": {"type": "string"}}}
        })
        self.state.context["authorized_tools"] = json.dumps(docs, ensure_ascii=False)

    def _format_observation(self, tool_name: str, result: Any) -> str:
        import json
        from pydantic import BaseModel
        data = result.model_dump() if isinstance(result, BaseModel) else result
        return json.dumps(data, ensure_ascii=False)
