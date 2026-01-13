"""
智能体执行引擎 (Agent Executor Kernel)

职责: 驱动智能体实体的多轮 ReAct 逻辑循环。
集成中间件架构、Session 级拓扑融合及任务进度催办机制，实现工业级的可靠编排。
"""

import json
from typing import AsyncGenerator, Dict, Any, List, Optional

from core.agent.agent import Agent
from core.agent.state import AgentStatus
from core.schema.message import AgentMessage, MessageRole
from core.llm.manager import llm_manager
from core.llm.schema import LLMMessage, LLMRole, InferenceConfig
from core.llm.resolver import config_resolver
from core.protocol.parser import ProtocolParser
from core.prompt.compiler import prompt_compiler
from core.orchestrator.pipeline import WorkflowPipeline
from core.orchestrator.schema import NodeStatus
from core.schema.orchestration import WorkflowManifest, TaskNode
from core.middleware.manager import middleware_manager

class AgentExecutor:
    """
    智能体逻辑执行驱动器。
    """

    def __init__(self):
        self.parser = ProtocolParser()

    async def run(self, agent: Agent, input_text: Optional[str] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        驱动 ReAct 循环生命周期。
        """
        session = agent.session
        profile = agent.profile
        middlewares = middleware_manager.assemble(agent)

        # 1. 动态路由算力资源
        try:
            llm_config = config_resolver.resolve(agent.agent_id)
            llm_client = llm_manager.create_client(llm_config)
            session.update_metadata("llm_provider", llm_config.provider_type)
            session.update_metadata("llm_model", llm_config.model)
        except Exception as e:
            yield {"type": "error", "content": f"算力资源分配失败: {str(e)}"}
            return

        # 2. 装配执行期能力集
        self._prepare_capability_mask(agent)

        # 3. 触发启动钩子
        for mw in middlewares:
            await mw.on_agent_start(session, profile)

        # 4. 挂载初始用户指令
        if input_text:
            session.add_message(AgentMessage(role=MessageRole.USER, content=input_text))

        # 5. 执行多轮编排循环
        max_steps = profile.max_turns
        for step in range(max_steps):
            session.update_metadata("status", AgentStatus.THINKING) 
            
            # A. 指令编译
            system_prompt = prompt_compiler.compile_agent_prompt(profile, session)
            session.update_metadata("last_system_prompt", system_prompt)
            
            # B. 构造消息序列
            messages = []
            for m in session.history:
                if m.role == MessageRole.TOOL:
                    # [关键修复] 将观察结果标准化为 USER 消息
                    # 确保 ReAct 闭环中模型能无歧义地读取到执行结果，不依赖特定 API 的 Tool 协议
                    formatted_content = f"[{m.name or 'System Observation'}]\n{m.content}"
                    messages.append(LLMMessage(role=LLMRole.USER, content=formatted_content))
                else:
                    messages.append(LLMMessage(role=LLMRole(m.role.value), content=m.content))
            
            # 触发: pre_inference
            for mw in middlewares:
                await mw.pre_inference(session, messages)
            
            # C. 发起流式推理
            full_response = ""
            async for chunk in llm_client.stream(
                messages=messages, 
                system=system_prompt,
                config=InferenceConfig(**profile.inference_params)
            ):
                full_response += chunk
                yield {"type": "stream", "content": chunk}

            # D. 解析响应意图
            proto = self.parser.parse(full_response)
            
            # 触发: post_inference
            for mw in middlewares:
                await mw.post_inference(session, proto)

            session.add_message(AgentMessage(role=MessageRole.ASSISTANT, content=full_response))

            # --- 核心反馈循环: 协议审计与回滚 ---
            if proto.errors:
                human_friendly_errors = self._translate_protocol_errors(proto.errors)
                error_feedback = (
                    "[协议指令审计失败] 您的回复格式存在违约，请修正后重新输出:\n"
                    f"{human_friendly_errors}\n"
                    "请检查 JSON 字段名（必须是 capability 和 arguments）及结构完整性。"
                )
                session.add_message(AgentMessage(role=MessageRole.TOOL, content=error_feedback, name="protocol_auditor"))
                yield {"type": "status", "content": "检测到指令格式违约，正在引导模型修正..."}
                continue 

            # E. 决策路径分发
            if proto.conclusion:
                session.update_metadata("status", AgentStatus.COMPLETED)
                yield {"type": "conclusion", "content": proto.conclusion}
                break

            if proto.dispatch:
                if not proto.blueprint:
                    error_msg = "[协议异常] 检测到派发意图 (<dispatch>) 但缺失任务蓝图清单 (<blueprint>)。请在派发任务前先定义拓扑结构。"
                    session.add_message(AgentMessage(role=MessageRole.TOOL, content=error_msg, name="protocol_auditor"))
                    continue

                session.update_metadata("status", AgentStatus.ACTING)
                
                # 诊断：记录分发动作
                print(f"\033[93m[Executor Trace] 检测到调度意图，准备驱动 Pipeline。待执行节点数: {len(proto.dispatch)}\033[0m")
                
                # 触发: pre_dispatch
                for mw in middlewares:
                    await mw.pre_dispatch(session, proto)
                
                # 启动编排管线并融合历史
                session_manifest = self._fuse_orchestration(session, proto.blueprint)
                pipeline = WorkflowPipeline(session_manifest, session, proto.dispatch)
                snapshot = await pipeline.execute()
                
                # --- 【增强日志】：显式打印物理调用详情 ---
                print(f"\033[1;34m[Physical Execution Summary]\033[0m")
                for node_id, result in snapshot.results.items():
                    status_icon = "✅" if result.status == "success" else "❌"
                    print(f"  {status_icon} Node: {node_id} | Capability: {session_manifest.nodes[0].capability if session_manifest.nodes else 'unknown'}")
                
                # 触发: post_dispatch
                for mw in middlewares:
                    await mw.post_dispatch(session, snapshot)

                # --- 【关键同步】：将 Pipeline 执行后的最新状态回填至 Session Metadata ---
                # 这样下一轮 ReAct 循环时，PromptCompiler 就能感知到哪些节点已完成
                local_nodes = session.get_metadata("session_blueprint_nodes", {})
                for node_id, result in snapshot.results.items():
                    if node_id in local_nodes:
                        local_nodes[node_id]["status"] = "COMPLETED" if result.status == "success" else "FAILED"
                        local_nodes[node_id]["output"] = result.output if result.status == "success" else result.error
                session.update_metadata("session_blueprint_nodes", local_nodes)

                # 1. 回注执行结果 (不再过滤，捕获 Pipeline 全量产出)
                print(f"\033[93m[Executor Trace] Pipeline 执行结束。正在回注所有观测结果...\033[0m")
                executed_count = 0
                for node_id, result in snapshot.results.items():
                    executed_count += 1
                    obs = str(result.output) if result.status == "success" else f"ERROR: {result.error}"
                    session.add_message(AgentMessage(
                        role=MessageRole.TOOL, 
                        content=obs, 
                        name=node_id, 
                        tool_call_id=node_id
                    ))
                    yield {"type": "observation", "content": obs, "source": node_id}
                
                print(f"\033[93m[Executor Trace] 已回注 {executed_count} 条 Observation。准备进入下一轮 ReAct 循环。\033[0m")
                
                # [Clean ReAct] 移除所有显式催办逻辑
                # 模型将基于上一步的 Observation 和 Context 中的 BluePrint 自动规划下一步
                continue 

            # 既无结论也无分派
            break

        # 循环结束
        for mw in middlewares:
            await mw.on_agent_end(session)

    def _translate_protocol_errors(self, errors: List[str]) -> str:
        """将校验报错翻译为具备行动指引的指令。"""
        translations = []
        for err in errors:
            if "capability" in err:
                translations.append("- 节点定义中缺少核心能力标识 'capability'。")
            elif "arguments" in err:
                translations.append("- 任务派发中缺少执行参数负载 'arguments'。")
            elif "blueprint" in err:
                translations.append("- 工作流蓝图结构非法或 JSON 报文截断。")
            else:
                translations.append(f"- 违约详情: {err}")
        return "\n".join(translations)

    def _fuse_orchestration(self, session: Any, new_manifest: WorkflowManifest) -> WorkflowManifest:
        """
        会话级拓扑融合。
        确保在合并新蓝图时，保留已完成节点的执行状态。
        """
        from core.schema.orchestration import WorkflowManifest, TaskNode
        local_nodes = session.get_metadata("session_blueprint_nodes", {})
        
        for node in new_manifest.nodes:
            # 如果该节点在本地已存在且状态为 COMPLETED，则保留状态，仅更新可能的定义变化
            if node.id in local_nodes:
                existing = local_nodes[node.id]
                node_dict = node.model_dump()
                node_dict["status"] = existing.get("status", "PENDING")
                node_dict["output"] = existing.get("output")
                local_nodes[node.id] = node_dict
            else:
                local_nodes[node.id] = node.model_dump()
                local_nodes[node.id]["status"] = "PENDING"
            
        session.update_metadata("session_blueprint_nodes", local_nodes)
        
        return WorkflowManifest(
            workflow_metadata=new_manifest.workflow_metadata,
            nodes=[TaskNode.model_validate(n) for n in local_nodes.values()]
        )

    def _prepare_capability_mask(self, agent: Agent):
        import json
        from core.tools.registry import tool_registry
        from core.agent.registry import agent_registry
        mask = agent.profile.capability_mask
        capabilities = []
        for tool_name, t in tool_registry._tools.items():
            if not mask or tool_name in mask:
                capabilities.append(t.to_openai_format()["function"])
        for agent_id in agent_registry.get_agents():
            if agent_id != agent.agent_id and (not mask or agent_id in mask):
                sub_profile = agent_registry.get_profile(agent_id)
                if sub_profile:
                    capabilities.append({
                        "name": sub_profile.agent_id,
                        "description": f"[智能体专家] {sub_profile.role_description}",
                        "parameters": {
                            "type": "object",
                            "properties": {"instruction": {"type": "string"}},
                            "required": ["instruction"]
                        }
                    })
        agent.session.update_metadata("authorized_tools", json.dumps(capabilities, ensure_ascii=False))
