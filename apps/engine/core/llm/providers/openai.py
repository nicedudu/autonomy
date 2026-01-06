from typing import AsyncGenerator, Dict, List, Any
from openai import OpenAI, AsyncOpenAI
from core.llm.providers.base import LLMProviderAdapter, ProviderResponse, ProviderUsage

class OpenAIAdapter(LLMProviderAdapter):
    """OpenAI 原生协议驱动，基于最新的 Responses API。"""
    
    def __init__(self, api_key: str, base_url: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.async_client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    def _prepare_payload(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """将通用消息格式转换为 Responses API 结构。"""
        instructions = next((m["content"] for m in messages if m["role"] == "system"), None)
        inputs = [{
            "role": m["role"],
            "content": [{"type": "text", "text": m["content"]}]
        } for m in messages if m["role"] != "system"]
        
        return {"instructions": instructions, "input": inputs}

    async def stream(
        self, 
        model: str, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """异步流式输出。直接透传经过校验的推理参数。"""
        payload = self._prepare_payload(messages)
        
        stream = await self.async_client.responses.create(
            model=model,
            stream=True,
            **payload,
            **kwargs
        )
        
        async for event in stream:
            if event.type == "response.text.delta":
                yield event.delta

    def call(
        self, 
        model: str, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> ProviderResponse:
        """同步阻塞调用。"""
        payload = self._prepare_payload(messages)
        res = self.client.responses.create(
            model=model,
            **payload,
            **kwargs
        )
        
        output = []
        for item in res.output:
            if item.type == "text":
                output.append({"content": item.text, "role": "assistant"})
            elif item.type == "tool_call":
                output.append({"type": "tool_call", "data": item.model_dump()})

        usage = ProviderUsage(
            input_tokens=res.usage.input_tokens,
            output_tokens=res.usage.output_tokens,
            total_tokens=res.usage.total_tokens
        ) if res.usage else ProviderUsage()

        return ProviderResponse(
            id=res.id,
            model=res.model,
            status=res.status,
            output=output,
            usage=usage
        )
