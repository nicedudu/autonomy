import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class Message(BaseModel):
    """Agent间通信消息模型"""
    sender: str
    recipient: str
    subject: str
    content: Dict[str, Any]
    timestamp: float = time.time()
    message_type: str = "private"  # private, broadcast, meeting
    meeting_id: Optional[str] = None

class ToolCall(BaseModel):
    """工具调用模型"""
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

from core.llm_factory import LLMFactory
from core.prompt_manager import PromptManager

class BaseAgent:
    """所有Agent的基础类"""
    
    def __init__(self, agent_id: str, agent_type: str, name: str, tools: List[str] = None):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.name = name
        self.tools = tools or []
        self.memory = []  # 短期记忆
        self.long_term_memory = None  # 长期记忆
        self.communication_bus = None  # 通信总线
        self.reasoning_engine = None  # 思考引擎
        self.llm_factory = LLMFactory() # 初始化模型工厂
        self.prompt_manager = PromptManager() # 初始化 Prompt 管理器
        self.last_action = None
        self.last_observation = None
        
        # 从 Prompt 库加载 System Prompt
        # 如果库里没有，再回退到默认值
        self.system_prompt = self.prompt_manager.get_system_prompt(agent_type)
        if not self.system_prompt:
             # 回退逻辑
             agent_config = self.llm_factory.get_agent_config(agent_type)
             self.system_prompt = agent_config.get("system_prompt", f"You are a helpful AI Agent named {name}.")

    def ask_llm(self, prompt: str, system_override: Optional[str] = None) -> str:
        """调用配置好的 LLM 进行推理"""
        messages = [
            {"role": "system", "content": system_override or self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        response = self.llm_factory.call_llm(self.agent_type, messages)
        
        # 记录 Token 使用情况到记忆中
        self.memory.append({
            "type": "llm_usage",
            "model": response.model,
            "usage": response.usage,
            "timestamp": time.time()
        })
        
        return response.content

    def set_memory_system(self, memory_system):
        """设置长期记忆系统"""
        self.long_term_memory = memory_system
    
    def set_communication_bus(self, communication_bus):
        """设置通信总线"""
        self.communication_bus = communication_bus
    
    def set_reasoning_engine(self, reasoning_engine):
        """设置思考引擎"""
        self.reasoning_engine = reasoning_engine
    
    def receive_message(self, message: Message):
        """接收消息"""
        print(f"[{self.name}] 收到来自 {message.sender} 的消息: {message.subject}")
        self.memory.append({
            "type": "message",
            "content": message,
            "timestamp": time.time()
        })
        self.process_message(message)
    
    def process_message(self, message: Message):
        """处理消息（子类实现）"""
        pass
    
    def send_message(self, recipient: str, subject: str, content: Dict[str, Any], message_type: str = "private"):
        """发送消息"""
        if not self.communication_bus:
            raise Exception("通信总线未初始化")
        
        message = Message(
            sender=self.agent_id,
            recipient=recipient,
            subject=subject,
            content=content,
            message_type=message_type
        )
        
        self.memory.append({
            "type": "sent_message",
            "content": message,
            "timestamp": time.time()
        })
        
        return self.communication_bus.send_message(message)
    
    def broadcast_message(self, subject: str, content: Dict[str, Any]):
        """广播消息"""
        return self.send_message("all", subject, content, "broadcast")
    
    def call_tool(self, tool_name: str, parameters: Dict[str, Any], thought: str = "") -> ActionResult:
        """调用工具"""
        if tool_name not in self.tools:
            raise Exception(f"工具 {tool_name} 不可用")
        
        # 实际工具调用将通过工具管理器进行，这里先返回模拟结果
        print(f"[{self.name}] 调用工具: {tool_name}, 参数: {parameters}, 思考: {thought}")
        
        # 模拟工具执行
        result = {
            "tool_name": tool_name,
            "success": True,
            "result": f"{tool_name} 执行成功，参数: {parameters}",
            "execution_time": 0.5
        }
        
        action_result = ActionResult(**result)
        
        self.memory.append({
            "type": "tool_call",
            "tool_name": tool_name,
            "parameters": parameters,
            "thought": thought,
            "result": action_result,
            "timestamp": time.time()
        })
        
        self.last_action = {
            "tool_name": tool_name,
            "parameters": parameters,
            "thought": thought
        }
        self.last_observation = action_result
        
        return action_result
    
    def think(self, task: str, context: Dict[str, Any] = None) -> List[ToolCall]:
        """思考过程（子类实现）"""
        raise NotImplementedError("子类必须实现think方法")
    
    def act(self, tool_calls: List[ToolCall]) -> List[ActionResult]:
        """执行动作"""
        results = []
        for tool_call in tool_calls:
            result = self.call_tool(
                tool_name=tool_call.tool_name,
                parameters=tool_call.parameters,
                thought=tool_call.thought
            )
            results.append(result)
        return results
    
    def observe(self, results: List[ActionResult]):
        """观察结果"""
        for result in results:
            print(f"[{self.name}] 观察到工具结果: {result.tool_name} - {'成功' if result.success else '失败'}")
    
    def plan(self, task: str) -> List[Dict[str, Any]]:
        """制定计划（子类实现）"""
        raise NotImplementedError("子类必须实现plan方法")
    
    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行任务的主循环"""
        print(f"[{self.name}] 开始执行任务: {task}")
        
        # 1. 思考
        tool_calls = self.think(task, context)
        
        # 2. 执行
        results = self.act(tool_calls)
        
        # 3. 观察
        self.observe(results)
        
        # 4. 反思
        self.reflect(task, results)
        
        return {
            "task": task,
            "success": all(result.success for result in results),
            "results": [result.model_dump() for result in results],
            "agent_id": self.agent_id
        }
    
    def reflect(self, task: str, results: List[ActionResult]):
        """反思过程（可选，子类实现）"""
        pass
    
    def self_improve(self, feedback: Dict[str, Any]):
        """自我改进（可选，子类实现）"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """获取Agent状态"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "name": self.name,
            "tools": self.tools,
            "memory_count": len(self.memory),
            "last_action": self.last_action,
            "last_observation": self.last_observation.model_dump() if self.last_observation else None
        }
