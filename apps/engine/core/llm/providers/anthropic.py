from typing import AsyncGenerator, Dict, List, Optional

from anthropic import Anthropic, AsyncAnthropic
from core.llm.providers.base import LLMProviderAdapter, ProviderResponse, ProviderUsage


class AnthropicAdapter(LLMProviderAdapter):
    """Anthropic Messages API 协议驱动。"""

    def __init__(self, api_key: str, base_url: str):
        self.client = Anthropic(api_key=api_key, base_url=base_url)
        self.async_client = AsyncAnthropic(api_key=api_key, base_url=base_url)

    def _extract_messages(self, messages: List[Dict[str, str]]) -> tuple[Optional[str], List[Dict[str, str]]]:
        """分离系统指令与对话消息。"""
        system_instruction = None
        filtered_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            else:
                role = "assistant" if msg["role"] in [
                    "model", "assistant", "agent"] else "user"
                filtered_messages.append(
                    {"role": role, "content": msg["content"]})

        return system_instruction, filtered_messages

    async def stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """异步流式响应实现。直接透传外部校验后的推理参数。"""
        system, user_msgs = self._extract_messages(messages)

        async with self.async_client.messages.stream(
            model=model,
            system=system,
            messages=user_msgs,
            **kwargs
        ) as stream:
            async for text in stream.text_stream:
                yield text

    def call(
        self,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> ProviderResponse:
        """同步阻塞调用实现。"""
        system, user_msgs = self._extract_messages(messages)

        res = self.client.messages.create(
            model=model,
            system=system,
            messages=user_msgs,
            **kwargs
        )

        output_items = []
        for content_block in res.content:
            if content_block.type == "text":
                output_items.append({
                    "content": content_block.text,
                    "role": res.role
                })
            elif content_block.type == "tool_use":
                output_items.append({
                    "type": "tool_use",
                    "id": content_block.id,
                    "name": content_block.name,
                    "input": content_block.input
                })

        usage = ProviderUsage(
            input_tokens=res.usage.input_tokens,
            output_tokens=res.usage.output_tokens,
            total_tokens=res.usage.input_tokens + res.usage.output_tokens
        )

        return ProviderResponse(
            id=res.id,
            model=model,
            output=output_items,
            usage=usage,
            finish_reason=res.stop_reason
        )
