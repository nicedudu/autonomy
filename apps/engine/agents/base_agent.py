import time
from typing import List, Dict, Any, Optional
from jinja2 import Template
from pydantic import BaseModel

from core.llm_factory import LLMFactory

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

class BaseAgent:
    """
    智能体通用基础类。
    支持单轮任务执行与多轮持续对话。
    """
    
    def __init__(self, agent_id: str, agent_type: str, name: str, tools: List[str] = None):
        """
        初始化智能体，加载配置并初始化对话历史。
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.name = name
        self.tools = tools or []
        self.memory = []
        self.long_term_memory = None
        self.communication_bus = None
        self.reasoning_engine = None
        self.llm_factory = LLMFactory()
        
        # 维护对话上下文
        self.chat_history: List[Dict[str, str]] = []
        
        # 加载核心提示词配置
        config = self.llm_factory.get_config(self.agent_id)
        self.system_prompt = config["system_prompt"]
        self.user_prompt_template = config["user_prompt"]

    def run(self, task_params: Dict[str, Any], clear_history: bool = True) -> str:
        """
        开启或重置一个基于模板的任务。
        """
        if clear_history:
            self.chat_history = []

        try:
            rendered_user_prompt = Template(self.user_prompt_template).render(**task_params)
        except Exception as e:
            raise RuntimeError(f"智能体 '{self.name}' 提示词渲染失败: {e}")

        return self.ask_llm(rendered_user_prompt)

    def chat(self, user_input: str) -> str:
        """
        在当前任务上下文中继续对话。
        """
        return self.ask_llm(user_input)

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
            display_content = content if len(content) < 500 else content[:500] + "..."
            print(f"[{role}]:\n{display_content}\n{'-'*40}")
        print(f"{ '='*60}\n")

        # 发起调用
        response = self.llm_factory.call_llm(self.agent_id, messages)
        
        # 更新历史记录
        self.chat_history.append({"role": "user", "content": prompt})
        self.chat_history.append({"role": "assistant", "content": response.content})

        return response.content

    # === 基础设施方法 ===

    def set_memory_system(self, memory_system):
        self.long_term_memory = memory_system
    
    def set_communication_bus(self, communication_bus):
        self.communication_bus = communication_bus
    
    def set_reasoning_engine(self, reasoning_engine):
        self.reasoning_engine = reasoning_engine
    
    def receive_message(self, message: Message):
        self.memory.append({
            "type": "received_message",
            "content": message.model_dump(),
            "timestamp": time.time()
        })
        self.process_message(message)
    
    def process_message(self, message: Message):
        pass
    
    def send_message(self, recipient: str, subject: str, content: Dict[str, Any], message_type: str = "private"):
        if not self.communication_bus:
            raise RuntimeError("通信总线未初始化。" )
        
        message = Message(
            sender=self.agent_id,
            recipient=recipient,
            subject=subject,
            content=content,
            message_type=message_type
        )
        return self.communication_bus.send_message(message)
    
    def call_tool(self, tool_name: str, parameters: Dict[str, Any], thought: str = "") -> ActionResult:
        if tool_name not in self.tools:
            raise ValueError(f"工具 '{tool_name}' 未授权。" )
        
        result = ActionResult(
            tool_name=tool_name,
            success=True,
            result=f"已模拟执行 {tool_name}",
            execution_time=0.1
        )
        return result

    def think(self, task: str, context: Dict[str, Any] = None) -> List[ToolCall]:
        raise NotImplementedError("子类必须实现 think 方法。" )
    
    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        tool_calls = self.think(task, context)
        results = [self.call_tool(tc.tool_name, tc.parameters, tc.thought) for tc in tool_calls]
        return {"task": task, "results": [r.model_dump() for r in results]}

    def get_status(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "history_turns": len(self.chat_history) // 2
        }