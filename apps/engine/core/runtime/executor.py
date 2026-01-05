import re
import json
import asyncio
import traceback
from typing import AsyncGenerator, Dict, Any, List
from core.schema.models import AgentManifest, ActionCall, ActionResult, Status
from core.registry.manager import discovery_service
from core.llm_factory import LLMFactory
from core.runtime.runner import ToolRunner
from core.middleware.base import AgentMiddleware
from core.middleware.logging import LoggingMiddleware
from core.middleware.stuck_loop import StuckLoopMiddleware
from core.middleware.planning import PlanningMiddleware

class AgentRuntime:
    """
    智能体生命周期驱动器。
    管理对话状态，通过中间件链和工具执行器驱动 Agent 完成多轮推理。
    """

    def __init__(self, manifest: AgentManifest):
        """初始化节点环境。"""
        self.manifest = manifest
        self.agent_id = manifest.agent_id
        self.name = manifest.name
        self.chat_history: List[Dict[str, str]] = []
        self.activated_skills: set = set()
        
        self.llm_factory = LLMFactory()
        self.tool_runner = ToolRunner()
        self.middlewares: List[AgentMiddleware] = [
            LoggingMiddleware(),
            StuckLoopMiddleware(),
            PlanningMiddleware()
        ]
        self.system_prompt = self._compile_prompt()

    def add_middleware(self, middleware: AgentMiddleware):
        """注册新中间件。"""
        self.middlewares.append(middleware)

    def _load_capability_docs(self) -> str:
        """从注册表提取并格式化当前节点被授权使用的能力文档。"""
        from tools import CORE_TOOLS
        import json
        
        docs = []
        # 1. 动态生成核心工具描述 (取代旧的 tools.json)
        docs.append("[核心工具 (CORE TOOLS)]")
        for tool in CORE_TOOLS:
            schema = tool.to_schema()
            docs.append(f"- `{schema['name']}`: {schema['description']}")
            docs.append(f"  参数 Schema: {json.dumps(schema['parameters'], ensure_ascii=False)}")

        # 2. 专项技能渐进式索引
        if self.manifest.capabilities:
            docs.append("\n[可用专项技能索引]")
            for skill_id in self.manifest.capabilities:
                docs.append(discovery_service.skills.get_index_docs([skill_id]))
                if skill_id in self.activated_skills:
                    docs.append(f"  --- 已激活 `{skill_id}` 执行手册 ---\n{discovery_service.skills.get_instruction(skill_id)}")
        
        return "\n".join(docs) if docs else "无可用能力"

    def _compile_prompt(self, team_roster: str = "", global_facts: List[str] = None) -> str:
        """组装系统级指令。"""
        from core.prompt_compiler import prompt_compiler
        
        capability_doc = self._load_capability_docs()
        prompt = prompt_compiler.compile_system_prompt(
            dynamic_capabilities=capability_doc, 
            team_roster=team_roster, 
            global_facts=global_facts
        )
        
        # --- 针对非主控节点的幕后模式约束 ---
        if self.agent_id != "primary_agent":
            prompt += "\n\n[幕后执行模式 - BACKEND MODE]\n"
            prompt += "你当前作为专项执行节点运行。你的受众是主控节点（Orchestrator），而非终端用户。\n"
            prompt += "1. 保持极度简洁，直接输出执行结果、数据或分析结论。\n"
            prompt += "2. 严禁使用任何社交辞令（如“你好”、“很高兴为你服务”）。\n"
            prompt += "3. 你必须维护全局计划状态（通过 <plan>），确保主控节点能感知你的进度。"

        if self.manifest.system_prompt_template:
            prompt += f"\n\n[角色专属指令]\n{self.manifest.system_prompt_template}"
        return prompt

    async def execute_async(self, prompt: str, team_roster: str = "", global_facts: List[str] = None, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """执行异步推理主循环。"""
        self.system_prompt = self._compile_prompt(team_roster=team_roster, global_facts=global_facts)
        
        for mw in self.middlewares:
            await mw.on_startup(self.agent_id, self.system_prompt)
        
        current_prompt = prompt
        max_turns = 15
        turn = 0

        try:
            while turn < max_turns:
                turn += 1
                messages = [{"role": "system", "content": self.system_prompt}]
                messages.extend(self.chat_history)
                messages.append({"role": "user", "content": current_prompt})

                # 思考前钩子
                current_messages = messages
                for mw in self.middlewares:
                    result = await mw.on_before_think(self.agent_id, current_messages)
                    if result is not None:
                        current_messages = result
                
                # 发起模型调用
                full_content = ""
                print(f"\n[{self.name}] 正在思考...", end="", flush=True)
                async for chunk in self.llm_factory.call_llm_stream_async(self.agent_id, current_messages, **kwargs):
                    print(chunk, end="", flush=True)
                    full_content += chunk
                    yield {"type": "stream", "agent_id": self.agent_id, "content": chunk}
                print("\n")
                
                for mw in self.middlewares:
                    full_content = await mw.on_after_think(self.agent_id, full_content)

                self.chat_history.append({"role": "user", "content": current_prompt})
                self.chat_history.append({"role": "assistant", "content": full_content})

                # 解析输出以决定下一步动作
                status_match = re.search(r"<status>(.*?)<\/status>", full_content, re.DOTALL)
                action_match = re.search(r"<action>(.*?)<\/action>", full_content, re.DOTALL)
                
                if status_match:
                    yield {"type": "status", "agent_id": self.agent_id, "content": status_match.group(1).strip()}

                if action_match:
                    try:
                        action = ActionCall(**json.loads(action_match.group(1).strip()))
                        for mw in self.middlewares:
                            await mw.on_before_action(self.agent_id, action)

                        # 执行工具
                        result = await self.tool_runner.run(action.tool_name, action.params)
                        
                        for mw in self.middlewares:
                            await mw.on_after_action(self.agent_id, action, result)
                        
                        # 观测结果反馈
                        from prompts.runtime import OBS_SUCCESS_TPL, OBS_FAIL_TPL
                        if result.status == Status.SUCCESS:
                            current_prompt = OBS_SUCCESS_TPL.format(
                                tool_name=action.tool_name, 
                                output_summary=str(result.output)[:5000]
                            )
                        else:
                            current_prompt = OBS_FAIL_TPL.format(
                                error=result.error
                            )
                        continue
                    except Exception as e:
                        current_prompt = f"\n[错误] 执行异常: {str(e)}"
                        continue
                break

            # 轮次耗尽处理
            if turn >= max_turns:
                from prompts.runtime import MAX_TURNS_PROMPT, FINAL_SUMMARY_INSTRUCTION
                yield {"type": "stream", "agent_id": self.agent_id, "content": MAX_TURNS_PROMPT}
                
                # 发起最后一轮总结
                messages = [{"role": "system", "content": self.system_prompt}, {"role": "user", "content": FINAL_SUMMARY_INSTRUCTION}]
                async for chunk in self.llm_factory.call_llm_stream_async(self.agent_id, messages):
                    yield {"type": "stream", "agent_id": self.agent_id, "content": chunk}

        except Exception as e:
            # === 全局异常屏障 (Global Exception Barrier) ===
            is_rate_limit = "429" in str(e)
            
            # 后端打印详细日志供排查
            if is_rate_limit:
                print(f"\n[Autonomy Core] 🛑 限流触发 (429): {str(e)}")
            else:
                print(f"\n[Autonomy Core] 💥 运行时异常:\n{traceback.format_exc()}")

            friendly_msg = "当前服务繁忙，请稍后重试。" if is_rate_limit else "系统运行异常，请联系管理员。"
            yield {"type": "error", "agent_id": self.agent_id, "content": friendly_msg}
        finally:
            for mw in self.middlewares:
                await mw.on_shutdown(self.agent_id)
