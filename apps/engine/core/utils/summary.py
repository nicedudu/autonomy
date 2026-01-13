"""
摘要引擎 (Summary Engine)

职责：负责将冗长的会话历史压缩为结构化的语义快照。
采用增量压缩策略，确保长上下文环境下的信息无损流转。
"""

from typing import List, Optional
from core.schema.message import AgentMessage, MessageRole
from core.llm.manager import llm_manager
from core.llm.schema import LLMMessage, LLMRole, InferenceConfig

class SummaryEngine:
    """
    语义压缩与摘要驱动器。
    """

    SUMMARY_PROMPT = (
        "你是一个专业的会话审计专家。请对以下对话历史进行『增量式摘要』。\n" 
        "要求：\n" 
        "1. 保留所有关键决策、已达成的结论以及重要的实体信息。\n" 
        "2. 保留当前正在进行的任务进度（正在做什么，下一步要做什么）。\n" 
        "3. 剔除所有礼貌用语、重复的指令以及冗长的推理过程。\n" 
        "4. 输出必须极度简洁，使用 Markdown 列表格式。\n" 
        "5. 如果存在之前的摘要，请将新信息融合进去，形成一份最新的全量快照。"
    )

    async def summarize(self, history: List[AgentMessage], previous_summary: Optional[str] = None) -> str:
        """
        对历史记录进行压缩。
        """
        if not history:
            return previous_summary or ""

        # 构造推理上下文
        context_text = ""
        if previous_summary:
            context_text += f"### 既往摘要快照:\n{previous_summary}\n\n"
        
        context_text += "### 新增交互记录:\n"
        for msg in history:
            role_label = "用户" if msg.role == MessageRole.USER else "智能体"
            name_label = f"({msg.name})" if msg.name else ""
            context_text += f"- {role_label}{name_label}: {msg.content[:500]}...\n"

        # 调用 LLM 进行压缩 (优先使用成本较低的模型)
        try:
            client = llm_manager.create_client(None)
            
            messages = [
                LLMMessage(role=LLMRole.SYSTEM, content=self.SUMMARY_PROMPT),
                LLMMessage(role=LLMRole.USER, content=context_text)
            ]
            
            summary_result = await client.ask(
                messages=messages,
                config=InferenceConfig(temperature=0.3, max_tokens=1024)
            )
            
            return summary_result.strip()
        except Exception as e:
            print(f"[SummaryEngine Error] 摘要提取失败: {str(e)}")
            return previous_summary or "摘要提取异常，请参考近期历史。"

summary_engine = SummaryEngine()