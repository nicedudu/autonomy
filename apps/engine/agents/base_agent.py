import time
import re
import json
from typing import Any, Dict, List, Optional, AsyncGenerator

from core.llm_factory import LLMFactory
from core.prompt_manager import PromptManager
from jinja2 import Template
from pydantic import BaseModel


class Message(BaseModel):
    """智能体间通信消息模型"""
    sender: str
    recipient: str
    subject: str
    content: Dict[str, Any]
    timestamp: float = time.time()
    message_type: str = "private"


class ToolCall(BaseModel):
    """工具调用请求模型"""
    tool_name: str
    parameters: Dict[str, Any]
    thought: str


class ActionResult(BaseModel):
    """工具执行结果模型"""
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: float


class AgentInterface(BaseModel):
    """定义智能体的输入输出契约"""
    input_schema: Dict[str, Any] = {}
    output_schema: Dict[str, Any] = {}

class AgentManifest(BaseModel):
    """
    Nexus V4 智能体清单
    定义智能体的人设、职责、接口契约与权限。
    """
    agent_id: str
    name: str
    role: str
    description: Optional[str] = None
    interface: AgentInterface = AgentInterface() # 新增：接口定义
    skills: List[str] = []
    allowed_tools: List[str] = []
    model: Optional[str] = None
    system_prompt_template: Optional[str] = None

class CollaborationCall(BaseModel):
    """
    [Nexus V4] 结构化协作调用协议 (Envelope)
    替代不稳定的纯文本 @ 提及。
    """
    target_id: str
    task: str
    params: Dict[str, Any] = {}
    priority: int = 1

class BaseAgent:
    """
    Autonomy Universal Executor (Nexus V4)
    统一智能体执行引擎，支持插件式技能挂载与状态感知。
    """

    def __init__(self, agent_id: str, agent_type: str = "general", name: str = None, manifest: AgentManifest = None):
        """
        初始化智能体。支持从 manifest 加载或从数据库传统加载。
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.manifest = manifest
        self.name = name or (manifest.name if manifest else "未知智能体")
        
        # 基础设施初始化
        self.llm_factory = LLMFactory()
        self.prompt_manager = PromptManager()
        self.communication_bus = None
        
        # 核心记忆与上下文
        self.chat_history: List[Dict[str, str]] = []
        self.current_skills: List[str] = manifest.skills if manifest else []
        
        # 加载初始配置
        self._load_config()

    def _load_config(self):
        """加载智能体配置"""
        if not self.manifest:
            raise RuntimeError(f"智能体 {self.agent_id} 启动失败：缺失 Manifest 清单。")
        
        self.system_prompt = self.manifest.system_prompt_template or ""
        self.user_prompt_template = "{{input}}"
        
        if not self.name:
            self.name = self.manifest.name

    def mount_skill(self, skill_id: str):
        """动态挂载新技能 (Nexus V4 特性)"""
        if skill_id not in self.current_skills:
            self.current_skills.append(skill_id)
            print(f"[{self.name}] 已挂载新技能: {skill_id}")

    def run(self, task_params: Dict[str, Any], clear_history: bool = True) -> str:
        """
        开启或重置一个基于模板的任务。
        """
        if clear_history:
            self.chat_history = []

        try:
            rendered_user_prompt = Template(
                self.user_prompt_template).render(**task_params)
        except Exception as e:
            raise RuntimeError(f"智能体 '{self.name}' 提示词渲染失败: {e}")

        return self.ask_llm(rendered_user_prompt)

    def chat(self, user_input: str) -> str:
        """
        在当前任务上下文中继续对话。
        """
        return self.ask_llm(user_input)

    async def chat_to_bus(self, user_input: str, recipient: str):
        """
        流式对话并将结果实时通过总线发送给接收者。
        """
        full_content = ""
        # ask_llm_stream 是同步生成器，我们在这里循环它
        for chunk in self.ask_llm_stream(user_input):
            full_content += chunk
            # 实时发送 chunk
            await self.send_message(
                recipient=recipient,
                subject="task_stream_chunk",
                content={
                    "chunk": chunk,
                    "full_content_so_far": full_content,
                    "status": "streaming"
                }
            )

        # 发送完成标志
        await self.send_message(
            recipient=recipient,
            subject="task_result",
            content={
                "result": full_content,
                "status": "completed"
            }
        )
        return full_content

    def chat_stream(self, user_input: str):
        """
        在当前任务上下文中继续对话（流式）。
        """
        return self.ask_llm_stream(user_input)

    async def chat_stream_async(self, user_input: str, **kwargs):
        """
        在当前任务上下文中继续对话（异步流式）。
        """
        async for chunk in self.ask_llm_stream_async(user_input, **kwargs):
            yield chunk

    def ask_llm(self, prompt: str) -> str:
        """
        统一的模型请求处理，自动维护对话历史并打印详细日志。
        """
        # 构建消息序列
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.chat_history)
        messages.append({"role": "user", "content": prompt})

        # --- 生产级调试日志 ---
        print(f"\n{'='*20} 发送至 LLM 的完整 Context {'='*20}")
        for msg in messages:
            role = msg["role"].upper()
            content = msg["content"]
            # 简单截断过长的内容以便阅读
            display_content = content if len(
                content) < 500 else content[:500] + "..."
            print(f"[{role}]:\n{display_content}\n{'-'*40}")
        print(f"{ '='*60}\n")

        # 发起调用
        response = self.llm_factory.call_llm(self.agent_id, messages)

        # 更新历史记录
        self.chat_history.append({"role": "user", "content": prompt})
        self.chat_history.append(
            {"role": "assistant", "content": response.content})

        print(f"\n{'-'*20} [{self.name}] 完整回复 {'-'*20}")
        print(response.content)
        print(f"{'-'*60}\n")

        return response.content

    def request_utility(self, system_prompt: str, user_prompt: str) -> str:
        """
        单次工具类请求，不记录对话历史。用于总结、翻译等辅助任务。
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        response = self.llm_factory.call_llm(self.agent_id, messages)
        return response.content

    def ask_llm_stream(self, prompt: str):
        """
        流式模型请求处理。
        """
        # 构建消息序列
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.chat_history)
        messages.append({"role": "user", "content": prompt})

        print(f"\n[{self.name}] 正在思考 (Stream):")
        full_content = ""
        for chunk in self.llm_factory.call_llm_stream(self.agent_id, messages):
            print(chunk, end="", flush=True)
            full_content += chunk
            yield chunk
        print("\n")  # 结束换行

        # 更新历史记录
        self.chat_history.append({"role": "user", "content": prompt})
        self.chat_history.append(
            {"role": "assistant", "content": full_content})

    async def ask_llm_stream_async(self, prompt: str, **kwargs):
        """
        异步流式模型请求处理 (Nexus V4 闭环推理引擎)
        支持 Thought-Action-Observation 循环。
        """
        # 1. 自动生成上下文快照
        snapshot = self._generate_context_snapshot() if len(self.chat_history) > 2 else ""
        system_content = self.system_prompt
        if snapshot:
            system_content += f"\n\n[CONTEXT_SNAPSHOT]\n{snapshot}\n"
        
        # 2. 核心推理循环
        current_user_prompt = prompt
        max_turns = 5
        turn = 0

        while turn < max_turns:
            turn += 1
            messages = [{"role": "system", "content": system_content}]
            messages.extend(self.chat_history)
            messages.append({"role": "user", "content": current_user_prompt})

            # 日志记录
            log_label = f"推理轮次 {turn}" if turn > 1 else ("结果反馈" if "专家" in prompt else "正在思考")
            print(f"\n[{self.name}] {log_label} (Async Stream):")
            
            full_content = ""
            async for chunk in self.llm_factory.call_llm_stream_async(self.agent_id, messages, **kwargs):
                print(chunk, end="", flush=True)
                full_content += chunk
                yield chunk
            print("\n")

            # 更新历史
            self.chat_history.append({"role": "user", "content": current_user_prompt})
            self.chat_history.append({"role": "assistant", "content": full_content})

            # 3. 动作识别 (Skill Use)
            action_match = re.search(r"<action>(.*?)<\/action>", full_content, re.DOTALL)
            if action_match:
                action_raw = action_match.group(1).strip()
                try:
                    import json
                    from core.skill_manager import skill_manager
                    action_data = json.loads(action_raw)
                    skill_id = action_data.get("skill_id")
                    params = action_data.get("params", {})
                    
                    if skill_id in self.current_skills:
                        yield f"\n\n[系统] 正在执行技能: {skill_id}...\n"
                        result = skill_manager.run_skill(skill_id, params)
                        
                        # 反馈观测结果
                        obs = f"[Observation] 技能 {skill_id} 返回结果: {json.dumps(result, ensure_ascii=False)}"
                        current_user_prompt = obs
                        continue # 进入下一轮循环
                    else:
                        current_user_prompt = f"[Error] 权限不足：未挂载技能 {skill_id}"
                        continue
                except Exception as e:
                    current_user_prompt = f"[Error] 动作解析失败: {str(e)}"
                    continue
            
            # 无动作或推理完成
            break

    def _generate_context_snapshot(self) -> str:
        """
        [Nexus V4] 生成基于 Qwen/Codex 理念的上下文快照。
        提炼对话历史中的关键事实、决策和待办。
        """
        # 目前先用简易逻辑，后期对接专门的 Summarizer Agent
        summary = "历史关键点:\n"
        for msg in self.chat_history[-4:]: # 仅提取最近两轮作为参考
            role = "董事长" if msg["role"] == "user" else self.name
            content = msg["content"]
            # 过滤掉标签
            clean_content = content[:100].replace("<thought>", "").replace("</thought>", "")
            summary += f"- {role}: {clean_content}...\n"
        
        return f"<snapshot>\n{summary}</snapshot>"

    # === 基础设施方法 ===

    def set_memory_system(self, memory_system):
        self.long_term_memory = memory_system

    def set_communication_bus(self, communication_bus):
        self.communication_bus = communication_bus

    def set_reasoning_engine(self, reasoning_engine):
        self.reasoning_engine = reasoning_engine

    async def receive_message(self, message: Message):
        self.memory.append({
            "type": "received_message",
            "content": message.model_dump(),
            "timestamp": time.time()
        })
        await self.process_message(message)

    async def process_message(self, message: Message):
        pass

    async def send_message(self, recipient: str, subject: str, content: Dict[str, Any], message_type: str = "private"):
        if not self.communication_bus:
            raise RuntimeError("通信总线未初始化。")

        message = Message(
            sender=self.agent_id,
            recipient=recipient,
            subject=subject,
            content=content,
            message_type=message_type
        )
        return await self.communication_bus.send_message(message)

    def call_tool(self, tool_name: str, parameters: Dict[str, Any], thought: str = "") -> ActionResult:
        if tool_name not in self.tools:
            raise ValueError(f"工具 '{tool_name}' 未授权。")

        result = ActionResult(
            tool_name=tool_name,
            success=True,
            result=f"已模拟执行 {tool_name}",
            execution_time=0.1
        )
        return result

    def think(self, task: str, context: Dict[str, Any] = None) -> List[ToolCall]:
        raise NotImplementedError("子类必须实现 think 方法。")

    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        tool_calls = self.think(task, context)
        results = [self.call_tool(
            tc.tool_name, tc.parameters, tc.thought) for tc in tool_calls]
        return {"task": task, "results": [r.model_dump() for r in results]}

    def get_status(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "history_turns": len(self.chat_history) // 2
        }
