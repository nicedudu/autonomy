"""
上下文管理中间件 (Context Management Middleware)

职责：实现基于滑动窗口和语义摘要的 Context Window 优化。
该版本仅负责状态维护与消息序列裁剪，最终摘要呈现由 PromptCompiler 负责。
"""

from typing import List
from core.middleware.base import BaseMiddleware
from core.session.session import Session
from core.llm.schema import LLMMessage
from core.utils.summary import summary_engine

class ContextMiddleware(BaseMiddleware):
    """
    分层记忆管理中间件。
    """
    priority: int = 10 

    MAX_HISTORY_LEN = 15  
    WINDOW_SIZE = 8       

    async def pre_inference(self, session: Session, messages: List[LLMMessage]):
        """
        在推理发起前，检查历史长度并进行语义压缩。
        """
        history = session.history
        
        if len(history) <= self.MAX_HISTORY_LEN:
            return

        print(f"\033[94m[ContextMiddleware] 检测到会话历史超限 ({len(history)})，启动语义压缩...\033[0m")

        # 1. 提取需要被压缩的消息
        to_summarize = history[:-self.WINDOW_SIZE]

        # 2. 执行增量摘要并存储到元数据
        previous_summary = session.get_metadata("history_summary")
        new_summary = await summary_engine.summarize(to_summarize, previous_summary)
        session.update_metadata("history_summary", new_summary)
        
        # 3. 裁剪当前发送给 LLM 的 messages 序列
        # 注意：messages[0] 通常是 System Prompt，我们保留它
        # 剩下的消息中，我们只保留最近的 WINDOW_SIZE 条
        
        system_msg = messages[0]
        recent_messages = messages[-self.WINDOW_SIZE:]
        
        # 原地更新 messages 列表
        messages.clear()
        messages.append(system_msg)
        messages.extend(recent_messages)

        print(f"\033[94m[ContextMiddleware] 历史裁剪完成。已保留最近 {len(recent_messages)} 条交互。摘要已同步至元数据。\033[0m")
