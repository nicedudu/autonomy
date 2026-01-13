import json
from typing import List, Any
from core.llm.schema import LLMMessage
from core.middleware.base import BaseMiddleware
from core.protocol.schema import ProtocolResponse
from core.session.session import Session

class LoggingMiddleware(BaseMiddleware):
    priority: int = 0

    async def pre_inference(self, session: Session, messages: List[LLMMessage]):
        turn_index = (len(session.history) // 2) + 1
        agent_id = session.get_metadata("agent_id", "unknown")
        
        print(f"\n" + "="*40 + f" ROUND {turn_index} " + "="*40)
        print(f"DRIVEN BY: {agent_id}")
        
        # 输出全量系统提示词
        system_prompt = session.get_metadata("last_system_prompt", "N/A")
        print(f"\n--- [REAL LLM INPUT START] ---\\n")
        print(f"SYSTEM:\n{system_prompt}\n")
        
        print(f"MESSAGES:")
        for m in messages:
            print(f"[{m.role.value.upper()}]:\n{m.content}\n")
        print(f"--- [REAL LLM INPUT END] ---\\n")

    async def post_inference(self, session: Session, proto: ProtocolResponse):
        # 仅输出最原始的模型响应，不做任何解析展示
        print(f"\n--- [REAL LLM OUTPUT START] ---\\n")
        print(proto.raw_payload)
        print(f"\n--- [REAL LLM OUTPUT END] ---\\n")
        print("="*90 + "\n")

    async def on_agent_end(self, session: Session):
        # 任务结束标记
        status = session.get_metadata("status", "N/A")
        print(f"\n[MISSION END] Final Status: {status}\n")