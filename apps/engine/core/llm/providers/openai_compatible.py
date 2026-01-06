from typing import AsyncGenerator, Dict, List, Any
from openai import OpenAI, AsyncOpenAI
from core.llm.providers.base import LLMProviderAdapter, ProviderResponse, ProviderUsage

class OpenAICompatibleAdapter(LLMProviderAdapter):
    """标准 OpenAI 兼容协议驱动，基于 Chat Completions 接口。"""
    
    def __init__(self, api_key: str, base_url: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.async_client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def stream(
        self, 
        model: str, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """异步流式输出。"""
        stream = await self.async_client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            **kwargs
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def call(
        self, 
        model: str, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> ProviderResponse:
        """同步阻塞调用。"""
        res = self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=False,
            **kwargs
        )
        
        output = [{
            "content": choice.message.content,
            "role": choice.message.role,
            "tool_calls": choice.message.tool_calls
        } for choice in res.choices]

        usage = ProviderUsage(
            input_tokens=res.usage.prompt_tokens,
            output_tokens=res.usage.completion_tokens,
            total_tokens=res.usage.total_tokens
        ) if res.usage else ProviderUsage()

        return ProviderResponse(
            id=res.id,
            model=res.model,
            status="completed",
            output=output,
            usage=usage
        )