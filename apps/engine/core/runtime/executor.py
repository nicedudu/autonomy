import re
import json
import asyncio
from typing import AsyncGenerator, Dict, Any, List
from core.schema.models import AgentManifest, ActionCall, ActionResult, Status
from core.registry.manager import discovery_service
from core.llm_factory import LLMFactory

class AgentRuntime:
    """
    Autonomous execution environment for an agent.
    Manages instructions, conversation context, and the Thought-Action-Observation loop.
    """

    def __init__(self, manifest: AgentManifest):
        self.manifest = manifest
        self.agent_id = manifest.agent_id
        self.name = manifest.name
        self.chat_history: List[Dict[str, str]] = []
        self.llm_factory = LLMFactory()
        self.system_prompt = self._compile_prompt()

    def _load_capability_docs(self) -> str:
        """Extracts interface documentation for authorized node capabilities."""
        docs = []
        for skill_id in self.manifest.capabilities:
            skill = discovery_service.skills.get(skill_id)
            if skill:
                docs.append(f"- {skill.name} (`{skill.skill_id}`): {skill.description}")
                if skill.parameters:
                    docs.append(f"  Params: {json.dumps(skill.parameters, ensure_ascii=False)}")
        return "\n".join(docs) if docs else "None"

    def _compile_prompt(self) -> str:
        """
        Compiles the system prompt by merging the global base instruction,
        dynamic capability documentation, and the agent-specific role template.
        """
        from core.prompt_manager import prompt_manager
        base_instruction = prompt_manager.get_prompt("core_system_prompt")
        
        if not base_instruction:
            raise RuntimeError("CRITICAL: Base System Prompt missing in library.yaml.")

        # Injects authorized capability documentation
        capability_doc = self._load_capability_docs()
        prompt = base_instruction.replace("{{dynamic_capabilities}}", capability_doc)
        
        # Injects team roster for coordination
        prompt = prompt.replace("{{team_roster}}", "Currently operating as a standalone node.")
        
        # Appends role-specific instruction from manifest
        if self.manifest.system_prompt_template:
            prompt += f"\n\n[Role Specific Instruction]\n{self.manifest.system_prompt_template}"
            
        return prompt

    async def execute_async(self, prompt: str, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Main execution loop driving the Thought-Action-Observation cycle.
        Supports hot-reloading of system prompts.
        """
        # 核心改进：每次执行前重新合成提示词，确保 Admin 变更即时生效
        self.system_prompt = self._compile_prompt()
        
        current_prompt = prompt
        max_turns = 5
        turn = 0

        while turn < max_turns:
            turn += 1
            messages = [{"role": "system", "content": self.system_prompt}]
            messages.extend(self.chat_history)
            messages.append({"role": "user", "content": current_prompt})

            full_content = ""
            # 显式传递 manifest 中的 model 以覆盖默认设置
            llm_kwargs = {**kwargs}
            if self.manifest.model:
                llm_kwargs["model"] = self.manifest.model

            print(f"\n[{self.name}] Thinking...")
            async for chunk in self.llm_factory.call_llm_stream_async(self.agent_id, messages, **llm_kwargs):
                print(chunk, end="", flush=True)
                full_content += chunk
                yield {"type": "stream", "agent_id": self.agent_id, "content": chunk}
            print("\n")

            self.chat_history.append({"role": "user", "content": current_prompt})
            self.chat_history.append({"role": "assistant", "content": full_content})

            # 动作识别与执行
            action_match = re.search(r"<action>(.*?)<\/action>", full_content, re.DOTALL)
            if action_match:
                try:
                    action_raw = action_match.group(1).strip()
                    action_data = json.loads(action_raw)
                    
                    # 严格契约：仅支持 tool_name
                    action = ActionCall(**action_data)
                    
                    # 1. 内核内置工具
                    builtin_tools = ["web_search", "web_fetch", "researcher"]
                    
                    if action.tool_name in builtin_tools or action.tool_name in self.manifest.capabilities:
                        # --- 生产级入参日志 ---
                        print(f"\n{'>>'*5} [Tool In]: {action.tool_name} {'<<'*5}")
                        print(f"Args: {json.dumps(action.params, ensure_ascii=False, indent=2)}")
                        
                        # 物理执行
                        result = await self._run_tool(action.tool_name, action.params)
                        status_label = "SUCCESS" if result.status == Status.SUCCESS else "FAILED"
                        
                        # --- 生产级出参日志 ---
                        print(f"{'<<'*5} [Tool Out]: {action.tool_name} ({status_label})")
                        if result.status == Status.SUCCESS:
                            try:
                                if isinstance(result.output, (dict, list)):
                                    print(f"Data: {json.dumps(result.output, ensure_ascii=False, indent=2)}")
                                else:
                                    print(f"Data: {str(result.output)[:1000]}")
                            except:
                                print(f"Data: {str(result.output)[:1000]}")
                        else:
                            print(f"Error: {result.error}")
                        print(f"{'--'*30}\n")

                        current_prompt = f"\n[OBSERVATION - {status_label}]\n{result.model_dump_json()}"
                        continue
                    else:
                        print(f"🚫 [Auth Error] Unauthorized tool: {action.tool_name}")
                        current_prompt = f"[OBSERVATION - FAILED]\nPermission denied for tool: {action.tool_name}."
                        continue
                except Exception as e:
                    current_prompt = f"[OBSERVATION - FAILED]\nAction execution failed: {str(e)}"
                    continue
            
            break

    async def _run_tool(self, tool_name: str, params: Dict[str, Any]) -> ActionResult:
        """执行具体的工具代码逻辑 (鲁棒路径版)"""
        import importlib.util
        import os

        # 1. 精准定位 tools 目录
        # 路径逻辑：core/runtime/executor.py -> core/runtime/ -> core/ -> ../tools/
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        engine_root = os.path.dirname(os.path.dirname(current_file_dir))
        tools_dir = os.path.join(engine_root, "tools")
        
        tool_file = f"{tool_name}.py"
        file_path = os.path.join(tools_dir, tool_file)

        if not os.path.exists(file_path):
            print(f"[Executor] 路径错误: 找不到工具文件 {file_path}")
            return ActionResult(status=Status.FAILED, error=f"Tool implementation not found: {tool_file} at {file_path}")

        try:
            # 2. 动态加载模块
            module_name = f"runtime.impl.{tool_name}"
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 3. 执行入口函数 run
            if hasattr(module, "run"):
                if asyncio.iscoroutinefunction(module.run):
                    raw_result = await module.run(params)
                else:
                    raw_result = module.run(params)
                
                # 适配各种返回格式，确保 status 存在
                status = Status.SUCCESS if raw_result.get("status") == "success" or raw_result.get("success") else Status.FAILED
                
                return ActionResult(
                    status=status,
                    output=raw_result.get("output") or raw_result.get("result"),
                    error=raw_result.get("message") or raw_result.get("error"),
                    tool_name=tool_name
                )
            else:
                return ActionResult(status=Status.FAILED, error=f"Tool {tool_name} missing 'run' function.")

        except Exception as e:
            import traceback
            print(f"[Executor] 运行时崩溃:\n{traceback.format_exc()}")
            return ActionResult(status=Status.FAILED, error=f"Runtime Error: {str(e)}")
