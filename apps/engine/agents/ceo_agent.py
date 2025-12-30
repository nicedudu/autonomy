from typing import List, Dict, Any, Optional
import time
import re
import asyncio
from agents.base_agent import BaseAgent, Message

class CEOAgent(BaseAgent):
    """
    首席执行官 Agent (CEO)
    作为团队领导者，负责多维度思考和任务分配。
    """
    
    def __init__(self, agent_id: str, name: str):
        # CEO 可能会用到所有核心工具，或者作为指挥官调用其他 Agent
        tools = ["Profit_Calculator"] 
        super().__init__(agent_id=agent_id, agent_type="ceo", name=name, tools=tools)
        
        # 加载 CEO 专属的系统提示词
        self.system_prompt = self.prompt_manager.get_system_prompt("ceo")

    def chat_stream(self, user_input: str):
        """
        覆盖父类的 chat_stream，增加 @mention 解析和任务分发逻辑。
        """
        full_response = ""
        for chunk in super().ask_llm_stream(user_input):
            full_response += chunk
            yield chunk

        # 在流结束后，解析回复中的 @mentions 并异步发送指令
        # 使用 create_task 以便不阻塞当前的同步流生成器（虽然流已经结束）
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self._delegate_tasks(full_response))
        except Exception as e:
            print(f"[CEO] 启动异步任务分发失败: {e}")

    async def _delegate_tasks(self, text: str):
        """
        解析文本中的 @agent_id 并在内部总线上分发任务。
        """
        # 匹配 @后面跟着字母数字下划线的格式，例如 @cpo_agent
        mentions = re.findall(r"@([a-zA-Z0-9_]+)", text)
        
        for agent_id in mentions:
            if agent_id == self.agent_id:
                continue
                
            print(f"[CEO] 检测到提及 {agent_id}，正在分发指令...")
            
            # 向被提及的智能体发送消息
            await self.send_message(
                recipient=agent_id,
                subject="task_delegation",
                content={
                    "instruction": text, 
                    "originator": self.agent_id
                }
            )

    async def process_message(self, message: Message):
        """
        处理来自成员的反馈。
        """
        sender = message.sender
        subject = message.subject
        content = message.content
        
        print(f"[CEO] 接收到来自 {sender} 的反馈: {subject}")
        
        if subject == "task_result":
            # 将最终反馈加入对话历史
            feedback_context = f"\n[收到来自 {sender} 的最终反馈]\n内容: {content.get('result')}"
            self.chat_history.append({"role": "system", "content": feedback_context})
        elif subject == "task_stream_chunk":
            # 这里可以选择是否记录流式 chunk，通常只打印或通过 WebSocket 转发
            # 转发逻辑已经在 api_server 的总线回调中处理了
            pass