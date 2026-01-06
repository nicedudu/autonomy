import asyncio
import uuid
import traceback
from typing import AsyncGenerator, Dict, Any, List, Optional
from core.agent.state import AgentState, AgentStatus, MessageRole, AgentMessage, StateUpdate
from core.agent.base import BaseAgent
from core.middleware.base import BaseMiddleware
from core.protocol.parser import ProtocolParser
from core.prompt.compiler import PromptCompiler
from core.tools.registry import tool_registry
from core.registry.internal import get_agent_definition

class AgentRuntime:
    """
    智能体协议执行引擎 (The Core Kernel)。
    """

    def __init__(
        self,
        agent: BaseAgent,
        middlewares: Optional[List[BaseMiddleware]] = None,
        max_steps: int = 15
    ):
        self.agent = agent
        self.middlewares = middlewares or []
        self.max_steps = max_steps
        self.state: Optional[AgentState] = None
        self.parser = ProtocolParser()
        self.compiler = PromptCompiler()

    async def run(
        self,
        input_text: Optional[str] = None,
        session_id: Optional[str] = None,
        existing_state: Optional[AgentState] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        驱动推理循环。
        """
        # 1. 初始化状态
        if existing_state:
            self.state = existing_state
        else:
            self.state = AgentState(
                agent_id=self.agent.agent_id,
                session_id=session_id or str(uuid.uuid4())
            )
            if input_text:
                self.state.add_message(MessageRole.USER, input_text)
        
        # 2. 合并外部传入的 Context 并准备工具文档
        if context:
            self.state.update_context(context)
        
        self._prepare_capabilities()

        step_count = 0
        try:
            while step_count < self.max_steps:
                step_count += 1
                self.state.status = AgentStatus.THINKING

                # --- Step A: Pre-Inference Middlewares ---
                for mw in self.middlewares:
                    update = await mw.pre_inference(self.state)
                    if update:
                        self.state.apply_update(update)

                # --- Step B: Compile Prompt & Think ---
                from core.prompt.compiler import prompt_compiler
                definition = get_agent_definition(self.agent.agent_id)
                system_prompt = prompt_compiler.compile_system_prompt(definition, self.state)
                
                # 将编译后的结果存入元数据，供 Logging 中间件打印
                self.state.metadata["compiled_system_prompt"] = system_prompt
                
                yield {"type": "event", "content": f"Step {step_count}: Reasoning...", "agent": self.agent.agent_id}
                
                # 注入最新的 System Prompt 执行推理
                thought_msg = await self.agent.think(self.state, system_prompt_override=system_prompt)
                
                # --- Step C: Post-Inference Middlewares ---
                for mw in self.middlewares:
                    update = await mw.post_inference(self.state, thought_msg.content)
                    if update:
                        self.state.apply_update(update)

                # 记录原始产出到历史
                self.state.history.append(thought_msg)
                yield {"type": "stream", "content": thought_msg.content, "agent": self.agent.agent_id}

                # --- Step D: Protocol Parsing & Action ---
                proto_res = self.parser.parse(thought_msg.content)
                
                # 处理结论 (Conclusion)
                if proto_res.conclusion:
                    self.state.status = AgentStatus.COMPLETED
                    yield {"type": "conclusion", "content": proto_res.conclusion}
                    break

                # 处理 A2A 委托 (Calls)
                if proto_res.calls:
                    self.state.status = AgentStatus.AWAITING_DELEGATION
                    for call in proto_res.calls:
                        yield {
                            "type": "delegation_event", 
                            "payload": call.model_dump(),
                            "tool_call_id": f"call_{call.target_id}"
                        }
                    return # 挂起当前运行时，移交控制权给 Orchestrator

                # 处理工具执行 (Actions)
                if proto_res.actions:
                    self.state.status = AgentStatus.ACTING
                    for action in proto_res.actions:
                        yield {"type": "event", "content": f"Executing tool: {action.tool_name}..."}
                        
                        tool = tool_registry.get_tool(action.tool_name)
                        if tool:
                            res = await tool.execute(**action.arguments)
                        else:
                            res = {"status": "error", "error": f"Tool '{action.tool_name}' not found."}

                        # 工具自愈逻辑：如果报错，将错误以 XML Observation 形式喂回给模型
                        obs_content = self._format_observation(action.tool_name, res)
                        self.state.add_message(MessageRole.TOOL, obs_content, tool_call_id=action.tool_name)
                        yield {"type": "observation", "content": obs_content}

                        # 执行 Action 后置中间件
                        for mw in self.middlewares:
                            update = await mw.on_action(self.state, action.model_dump(), res)
                            if update:
                                self.state.apply_update(update)
                else:
                    # 如果既没有 Action 也没有 Conclusion，可能是单纯的对话或模型迷失
                    # 在 Phase 4 我们保持循环，等待下一轮推理
                    if not proto_res.thought:
                        break 

            if step_count >= self.max_steps:
                self.state.status = AgentStatus.FAILED
                yield {"type": "error", "content": "Maximum reasoning steps reached."}

        except Exception as e:
            self.state.status = AgentStatus.FAILED
            yield {"type": "error", "content": f"Runtime exception: {str(e)}"}
            print(traceback.format_exc())

    def _prepare_capabilities(self):
        """
        根据 Agent 定义装配可用工具文档和智能体名录。
        """
        import json
        from core.registry.internal import INTERNAL_AGENTS
        definition = get_agent_definition(self.agent.agent_id)
        if not definition:
            return

        # 1. 装配工具文档
        docs = []
        for tool_name in definition.capabilities:
            tool = tool_registry.get_tool(tool_name)
            if tool:
                docs.append(f"<tool>\n  <name>{tool.name}</name>\n  <description>{tool.description}</description>\n  <arguments_schema>{json.dumps(tool.parameters, ensure_ascii=False)}</arguments_schema>\n</tool>")
        
        docs.append("<tool>\n  <name>delegate_to_agent</name>\n  <description>将任务委派给另一个专家节点。仅限下述名录中的 Agent ID。</description>\n  <arguments_schema>{\"target_id\": \"string\", \"task\": \"指令内容\", \"context\": {}}</arguments_schema>\n</tool>")
        self.state.context["skill_docs"] = "\n".join(docs)

        # 2. 装配智能体名录 (Roster)
        roster = ["可用专家名录:"]
        for aid, adef in INTERNAL_AGENTS.items():
            if aid != self.agent.agent_id: # 排除自己
                roster.append(f"- ID: {aid} ({adef.name}): {adef.role}")
        
        self.state.context["team_roster"] = "\n".join(roster)

    def _format_observation(self, tool_name: str, result: Any) -> str:
        """格式化工具产出，支持错误自愈。"""
        import json
        from core.tools.base import ToolResult
        
        # 1. 统一提取状态和数据
        status = "success"
        output_data = result
        error_msg = None

        if isinstance(result, ToolResult):
            status = result.status
            output_data = result.output
            error_msg = result.error
        elif isinstance(result, dict):
            status = result.get("status", "success")
            output_data = result.get("output", result)
            error_msg = result.get("error") or result.get("message")

        # 2. 处理错误分支 (触发模型自愈)
        if status == "error":
            return f"<observation status='error' tool='{tool_name}'>\nError: {error_msg}\nRecommendation: 请检查工具参数并重试，或尝试使用其他工具/调研方式。\n</observation>"
        
        # 3. 处理成功分支
        # 确保 output_data 是可序列化的 (如果是 Pydantic 对象则转换)
        if hasattr(output_data, "model_dump"):
            output_data = output_data.model_dump()
            
        return f"<observation status='success' tool='{tool_name}'>\n{json.dumps(output_data, ensure_ascii=False)}\n</observation>"
