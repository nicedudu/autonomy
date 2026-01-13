"""
Anthropic 算力供应商实现 (Anthropic Provider Implementation)

本模块实现了基于 Anthropic Claude 协议的适配器。
处理 Anthropic 特有的消息结构（如 System Prompt 剥离、多模态块处理）
并将其归一化为系统标准协议。
"""

import json
from typing import AsyncGenerator, List, Optional, Any, Dict, Union
from anthropic import AsyncAnthropic

from core.llm.base import BaseLLMProvider
from core.llm.schema import (
    LLMMessage, 
    LLMResponse, 
    InferenceConfig, 
    LLMRole, 
    LLMUsage, 
    ToolCall
)

class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic Claude 协议适配器。
    """

    def __init__(self, model: str, api_key: str, base_url: str, **kwargs):
        super().__init__(model, api_key, base_url, **kwargs)
        self.client = AsyncAnthropic(
            api_key=api_key,
            base_url=base_url if base_url else None,
            **self.client_options
        )

    async def generate(
        self, 
        messages: List[LLMMessage], 
        system: Optional[str] = None, 
        config: Optional[InferenceConfig] = None
    ) -> LLMResponse:
        """
        执行全量推理。
        """
        config = config or InferenceConfig()
        payload = self._to_anthropic_payload(messages)
        
        response = await self.client.messages.create(
            model=self.model,
            system=system if system else "",
            messages=payload,
            max_tokens=config.max_tokens or 4096,
            temperature=config.temperature,
            top_p=config.top_p,
            stop_sequences=config.stop,
            stream=False,
            **config.extra_params
        )

        # Anthropic 的 content 是一个列表，提取首个文本内容
        text_content = ""
        tool_calls = []
        
        for block in response.content:
            if block.type == "text":
                text_content += block.text
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=block.input
                ))

        return LLMResponse(
            content=text_content if text_content else None,
            tool_calls=tool_calls if tool_calls else None,
            model=response.model,
            usage=LLMUsage(
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
                total_tokens=response.usage.input_tokens + response.usage.output_tokens
            ),
            finish_reason=response.stop_reason,
            raw=response
        )

    async def stream(
        self, 
        messages: List[LLMMessage], 
        system: Optional[str] = None, 
        config: Optional[InferenceConfig] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式推理实现。
        """
        config = config or InferenceConfig()
        payload = self._to_anthropic_payload(messages)

        async with self.client.messages.stream(
            model=self.model,
            system=system if system else "",
            messages=payload,
            max_tokens=config.max_tokens or 4096,
            temperature=config.temperature,
            **config.extra_params
        ) as stream:
            async for text in stream.text_stream:
                yield text

    def _to_anthropic_payload(self, messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        """
        [内部私有] 标准消息转 Anthropic 格式。
        注意：Anthropic 不允许在 messages 列表中包含 system 角色。
        """
        payload = []
        for msg in messages:
            # 过滤掉系统消息（它们在 generate/stream 的顶层参数中处理）
            if msg.role == LLMRole.SYSTEM:
                continue
            
            item = {"role": msg.role.value, "content": msg.content}
            
            # 处理工具调用结果的回注 (Anthropic 特有)
            if msg.role == LLMRole.TOOL:
                item["role"] = "user" # 结果作为 user 角色回注
                item["content"] = [
                    {
                        "type": "tool_result",
                        "tool_use_id": msg.name, # 此时 msg.name 存的是 tool_call_id
                        "content": msg.content
                    }
                ]
            
            payload.append(item)
        return payload
