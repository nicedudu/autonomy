import json
from typing import Any, Dict

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

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
        from core.llm.service import LLMService
        from core.schema.models import LLMConfig
        from services.settings import SettingsService

        # 获取默认配置
        settings = SettingsService().get_system_settings()
        config = LLMConfig(
            provider="openai_compatible", # 假设默认
            model=settings.get("default_model", "gpt-4o"),
            api_key=settings.get("llm_providers", {}).get("api_token"),
            base_url=settings.get("llm_providers", {}).get("api_base")
        )

        llm_service = LLMService()
        messages = [
            {"role": "system", "content": "请将用户的输入总结为一个简短的标题（10字以内）。仅返回标题文本。"},
            {"role": "user", "content": content}
        ]
        
        response = llm_service.call(config, messages)
        # ProviderResponse.output 是一个包含 Dict 的 List
        if response.output and "content" in response.output[0]:
            title = response.output[0]["content"].strip().strip('"').strip("'")
        else:
            title = "新会话"
        return {"title": title}
    except Exception as e:
        print(f"Summarize failed: {e}")
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
