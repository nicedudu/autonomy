import json
import uuid
from typing import Any, Dict

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from api.deps import dispatcher

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("/summarize")
async def summarize_chat(request: Dict[str, Any]):
    """
    根据用户输入生成简短的会话标题。
    利用新版 llm_manager 执行高效总结。
    """
    content = request.get("content", "")
    if not content:
        return {"title": "新会话"}

    try:
        from core.llm.manager import llm_manager
        from core.llm.schema import LLMMessage, LLMRole
        from services.settings import SettingsService

        # 获取系统配置中的模型路由
        settings = SettingsService().get_system_settings()
        providers = settings.get("llm_providers", {})
        
        # 实例化新版模型客户端
        client = llm_manager.create_client(
            provider_type="openai_compatible", # 默认兼容协议
            api_key=providers.get("api_token", "sk-placeholder"),
            base_url=providers.get("api_base", "https://api.placeholder.com")
        )

        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content="请将用户的输入总结为一个简短的标题（10字以内）。仅返回标题文本，不要包含引号。"),
            LLMMessage(role=LLMRole.USER, content=content)
        ]
        
        # 执行全量生成
        response = await client.generate(
            messages=messages, 
            model=settings.get("default_model", "qwen-max")
        )
        
        return {"title": response.content.strip()}
    except Exception as e:
        print(f"Summarize failed via V3 core: {e}")
        return {"title": "新会话"}


@router.post("/stream")
async def chat_stream(request: Dict[str, Any]):
    """
    统一的流式执行入口。
    调度指定智能体执行任务，并以 NDJSON 格式返回流式推理结果。
    """
    agent_id = request.get("agent_id", "primary_agent")
    content = request.get("content", "")
    session_id = request.get("session_id", str(uuid.uuid4()))

    async def event_generator():
        async for event in dispatcher.execute_task(agent_id, content, session_id):
            yield json.dumps(event) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")
