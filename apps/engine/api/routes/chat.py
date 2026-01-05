from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from typing import Any, Dict
import json
from api.deps import orchestrator

router = APIRouter(prefix="/api/chat", tags=["Chat"])

@router.post("/summarize")
async def summarize_chat(request: Dict[str, Any]):
    """
    根据用户输入生成简短的会话标题。
    利用 LLM 将用户意图浓缩为 10 个词以内的总结。
    """
    content = request.get("content", "")
    if not content:
        return {"title": "新会话"}

    try:
        from core.llm_factory import LLMFactory
        llm_factory = LLMFactory()
        system_prompt = "You are a specialized secretary. Summarize the user's intent into a title under 10 words. Answer in the same language as the user input."
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ]
        response = llm_factory.call_default_llm(messages)
        title = response.content.strip().strip('"').strip("'")
        if len(title) > 50:
            title = title[:47] + "..."
        return {"title": title}
    except Exception as e:
        return {"title": "新会话"}

@router.post("/stream")
async def chat_stream(request: Dict[str, Any]):
    """
    统一的流式执行入口。
    调度指定智能体执行任务，并以 NDJSON 格式返回流式推理结果。
    """
    agent_id = request.get("agent_id", "primary_agent")
    content = request.get("content", "")

    async def event_generator():
        async for event in orchestrator.dispatch(agent_id, content):
            yield json.dumps(event) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")
