import json
from typing import AsyncGenerator, List, Optional, Any, Dict
from openai import AsyncOpenAI

from core.llm.base import BaseLLMProvider
from core.llm.schema import (
    LLMMessage, 
    LLMResponse, 
    InferenceConfig, 
    LLMUsage, 
    ToolCall
)

class OpenAICompatibleProvider(BaseLLMProvider):
    """
    通用 OpenAI 兼容协议适配器。
    """

    def __init__(self, model: str, api_key: str, base_url: str, **kwargs):
        super().__init__(model, api_key, base_url, **kwargs)
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            **self.client_options
        )

    async def generate(
        self, 
        messages: List[LLMMessage], 
        system: Optional[str] = None, 
        config: Optional[InferenceConfig] = None
    ) -> LLMResponse:
        config = config or InferenceConfig()
        payload = self._to_raw_payload(messages, system)
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=payload,
            temperature=config.temperature,
            top_p=config.top_p,
            max_tokens=config.max_tokens,
            stream=False,
            **config.extra_params
        )

        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content,
            tool_calls=self._parse_tool_calls(choice.message.tool_calls) if hasattr(choice.message, "tool_calls") and choice.message.tool_calls else None,
            model=response.model,
            usage=LLMUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens
            ),
            finish_reason=choice.finish_reason,
            raw=response
        )

    async def stream(
        self, 
        messages: List[LLMMessage], 
        system: Optional[str] = None, 
        config: Optional[InferenceConfig] = None
    ) -> AsyncGenerator[str, None]:
        config = config or InferenceConfig()
        payload = self._to_raw_payload(messages, system)

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=payload,
            stream=True,
            **config.extra_params
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def _to_raw_payload(self, messages: List[LLMMessage], system: Optional[str]) -> List[Dict[str, Any]]:
        """标准化协议转换。"""
        payload = []
        if system:
            payload.append({"role": "system", "content": system})
        for msg in messages:
            payload.append({"role": msg.role.value, "content": msg.content})
        return payload

    def _parse_tool_calls(self, raw_tool_calls: Any) -> List[ToolCall]:
        """解析兼容协议中的工具调用。"""
        if not raw_tool_calls: return []
        parsed = []
        for tc in raw_tool_calls:
            try:
                parsed.append(ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments)
                ))
            except Exception:
                continue
        return parsed