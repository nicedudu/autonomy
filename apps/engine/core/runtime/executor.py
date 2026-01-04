import re
import json
import asyncio
from typing import AsyncGenerator, Dict, Any, List
from core.schema.models import AgentManifest, ActionCall, ActionResult, Status
from core.registry.manager import discovery_service
from core.llm_factory import LLMFactory

class AgentRuntime:
    """
    智能体异步运行环境。
    负责指令集加载、对话上下文管理以及“思考-行动-观测”循环的驱动。
    """

    def __init__(self, manifest: AgentManifest):
        """
        初始化运行时。
        """
        self.manifest = manifest
        self.agent_id = manifest.agent_id
        self.name = manifest.name
        self.chat_history: List[Dict[str, str]] = []
        self.activated_skills: set = set() # 记录当前已激活的技能全文
        self.llm_factory = LLMFactory()
        self.system_prompt = self._compile_prompt()

    def _load_capability_docs(self) -> str:
        """从注册中心提取并格式化已授权的能力文档。"""
        import os
        import json
        
        docs = []
        
        # 1. 加载内置核心工具 (从 tools.json 读取接口契约)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        tools_json_path = os.path.join(os.path.dirname(os.path.dirname(current_dir)), "tools", "tools.json")
        
        try:
            if os.path.exists(tools_json_path):
                with open(tools_json_path, "r", encoding="utf-8") as f:
                    tools_meta = json.load(f)
                    docs.append("[核心工具 (CORE TOOLS)]")
                    for tool in tools_meta.get("core_tools", []):
                        docs.append(f"- `{tool['name']}`: {tool['description']}")
                        docs.append(f"  参数 Schema: {json.dumps(tool['parameters'], ensure_ascii=False)}")
        except Exception as e:
            print(f"[Executor] 加载 tools.json 失败: {e}")

        # 2. 动态加载的专项技能 (从 Registry 加载)
        if self.manifest.capabilities:
            docs.append("\n[可用专项技能索引 (SPECIALIZED SKILLS INDEX)]")
            docs.append("注：以下技能目前仅加载简介。如需使用，请在 <thought> 中声明激活该技能 ID。")
            
            for skill_id in self.manifest.capabilities:
                index_info = discovery_service.skills.get_index_docs([skill_id])
                docs.append(index_info)
                
                if skill_id in self.activated_skills:
                    full_instruction = discovery_service.skills.get_instruction(skill_id)
                    if full_instruction:
                        docs.append(f"  --- 已激活 `{skill_id}` 执行手册 ---")
                        docs.append(full_instruction)
                        docs.append("  --- 手册结束 ---\n")
        
        return "\n".join(docs) if docs else "无可用能力"

    def _compile_prompt(self) -> str:
        """
        合成系统提示词。
        """
        from core.prompt_manager import prompt_manager
        from datetime import datetime
        
        base_instruction = prompt_manager.get_prompt("core_system_prompt")
        if not base_instruction:
            raise RuntimeError("核心系统指令丢失，请检查 library.yaml 配置。")

        current_time = datetime.now().strftime("%Y-%m-%d %A %H:%M:%S")
        prompt = base_instruction.replace("{{current_time}}", current_time)

        capability_doc = self._load_capability_docs()
        prompt = prompt.replace("{{dynamic_capabilities}}", capability_doc)
        
        if self.manifest.system_prompt_template:
            prompt += f"\n\n[角色专属指令]\n{self.manifest.system_prompt_template}"
            
        return prompt

    async def execute_async(self, prompt: str, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        执行主循环。驱动模型进行多轮推理直至目标达成。
        """
        self.system_prompt = self._compile_prompt()
        
        current_prompt = prompt
        max_turns = 15 # 生产级上限
        turn = 0

        while turn < max_turns:
            turn += 1
            messages = [{"role": "system", "content": self.system_prompt}]
            messages.extend(self.chat_history)
            messages.append({"role": "user", "content": current_prompt})

            full_content = ""
            # 直接发起流式调用，参数合并由 LLMFactory 标准化处理
            print(f"\n[{self.name}] 正在思考 (第 {turn} 轮)...")
            async for chunk in self.llm_factory.call_llm_stream_async(self.agent_id, messages, **kwargs):
                print(chunk, end="", flush=True) # 实时打印模型原始输出
                full_content += chunk
                yield {"type": "stream", "agent_id": self.agent_id, "content": chunk}
            print("\n") # 换行，分隔不同轮次

            self.chat_history.append({"role": "user", "content": current_prompt})
            self.chat_history.append({"role": "assistant", "content": full_content})

            # 渐进式披露逻辑
            # ... (保持不变)

            # 动作识别与执行
            action_match = re.search(r"<action>(.*?)<\/action>", full_content, re.DOTALL)
            if action_match:
                try:
                    action_data = json.loads(action_match.group(1).strip())
                    action = ActionCall(**action_data)
                    
                    builtin_tools = ["web_search", "web_fetch", "researcher"]
                    if action.tool_name in builtin_tools or action.tool_name in self.manifest.capabilities:
                        
                        # --- 生产级入参日志 ---
                        print(f"\n{'>>'*5} [工具调用]: {action.tool_name} {'<<'*5}")
                        print(f"参数: {json.dumps(action.params, ensure_ascii=False, indent=2)}")
                        
                        result = await self._run_tool(action.tool_name, action.params)
                        
                        # --- 生产级出参日志 ---
                        status_label = "成功" if result.status == Status.SUCCESS else "失败"
                        print(f"{'<<'*5} [执行结果]: {action.tool_name} ({status_label})")
                        if result.status == Status.SUCCESS:
                            # 打印前 1000 字符的结果预览
                            print(f"数据摘要: {str(result.output)[:1000]}...")
                        else:
                            print(f"错误详情: {result.error}")
                        print("-" * 60 + "\n")
                        
                        if result.status == Status.SUCCESS:
                            obs_data = str(result.output)[:5000]
                            current_prompt = (
                                f"\n[观测结果 - 成功]\n"
                                f"工具 '{action.tool_name}' 执行完毕。\n"
                                f"输出摘要: {obs_data}\n\n"
                                f"指令: 请根据上述结果继续执行。如果信息已足够，请立即为用户合成最终答复。"
                            )
                        else:
                            current_prompt = f"\n[观测结果 - 失败]\n错误详情: {result.error}\n指令: 请尝试修复或向用户报告。"
                        continue
                    else:
                        current_prompt = f"\n[系统警告] 未授权工具: {action.tool_name}。"
                        continue
                except Exception as e:
                    current_prompt = f"\n[错误] 执行崩溃: {str(e)}"
                    continue
            break

        if turn >= max_turns:
            yield {
                "type": "stream", 
                "agent_id": self.agent_id, 
                "content": "\n\n⚠️ [系统提示] 已达到推理轮次上限。以下是阶段性总结：\n"
            }
            summary_prompt = "请根据目前已掌握的所有信息，为用户做一次最终的总结报告。"
            messages = [{"role": "system", "content": self.system_prompt}, {"role": "user", "content": summary_prompt}]
            async for chunk in self.llm_factory.call_llm_stream_async(self.agent_id, messages):
                yield {"type": "stream", "agent_id": self.agent_id, "content": chunk}

    async def _run_tool(self, tool_name: str, params: Dict[str, Any]) -> ActionResult:
        """动态加载并执行工具逻辑。"""
        import importlib.util
        import os

        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        engine_root = os.path.dirname(os.path.dirname(current_file_dir))
        tools_dir = os.path.join(engine_root, "tools")
        
        file_path = os.path.join(tools_dir, f"{tool_name}.py")
        if not os.path.exists(file_path):
            return ActionResult(status=Status.FAILED, error=f"工具文件不存在: {tool_name}")

        try:
            module_name = f"runtime.impl.{tool_name}"
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, "run"):
                if asyncio.iscoroutinefunction(module.run):
                    raw_result = await module.run(params)
                else:
                    raw_result = module.run(params)
                
                status = Status.SUCCESS if raw_result.get("status") == "success" or raw_result.get("success") else Status.FAILED
                return ActionResult(
                    status=status,
                    output=raw_result.get("output") or raw_result.get("result"),
                    error=raw_result.get("message") or raw_result.get("error"),
                    tool_name=tool_name
                )
            return ActionResult(status=Status.FAILED, error=f"工具 {tool_name} 缺少接口")
        except Exception as e:
            return ActionResult(status=Status.FAILED, error=f"运行时崩溃: {str(e)}")
