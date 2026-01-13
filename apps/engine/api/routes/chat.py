import json
import uuid
from typing import Any, Dict

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from api.deps import agent_service

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("/summarize")
async def summarize_chat(request: Dict[str, Any]):
    """
    根据用户输入生成简短的会话标题。
    """
    content = request.get("content", "")
    if not content:
        return {"title": "新会话"}

    try:
        from core.llm.manager import llm_manager
        from core.llm.schema import LLMMessage, LLMRole, LLMProviderConfig
        from services.settings import SettingsService

        # 1. 遵循 Admin 配置：直接从 SettingsService 获取系统默认路径
        settings_service = SettingsService()
        system_settings = settings_service.get_system_settings()
        
        # 2. 提取 Admin 设置的算力详情
        providers = system_settings.get("llm_providers", {})
        default_model = system_settings.get("default_model", "ministral-3:latest")
        
        # 3. 构造合法的算力载荷
        llm_config = LLMProviderConfig(
            provider_type=providers.get("type", "openai_compatible"),
            model=default_model,
            api_key=providers.get("api_token", "ollama"),
            base_url=providers.get("api_base", "http://localhost:11434/v1")
        )

        client = llm_manager.create_client(llm_config)

        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content="你是一个标题生成助手。请将用户输入总结为一个极其简短的标题（10字以内）。注意：仅返回纯文本，严禁包含任何 Markdown 格式、星号、括号、标题符或引号。"),
            LLMMessage(role=LLMRole.USER, content=content)
        ]
        
        # 执行总结
        response = await client.generate(
            messages=messages
        )
        
        # 后置净化：移除所有 Markdown 标记和标点
        import re
        title = response.content.strip()
        title = re.sub(r'[*#_`\[\]()\-+!>\n]', '', title) # 移除 Markdown 符号
        title = title.replace('"', '').replace('“', '').replace('”', '')
        
        return {"title": title if title else "新会话"}
    except Exception as e:
        import traceback
        print(f"\033[31m[Summarize Failed] Error: {str(e)}\033[0m")
        traceback.print_exc()
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
        async for event in agent_service.execute_task(agent_id, content, session_id):
            yield json.dumps(event) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")
