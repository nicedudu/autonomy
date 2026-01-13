"""
DeepSeek 算力供应商实现 (DeepSeek Provider Implementation)

本模块实现了针对 DeepSeek API 的优化适配。
虽然 DeepSeek 兼容 OpenAI 协议，但本适配器额外支持了其特有的
推理模型思维链 (Reasoning Content) 提取。
"""

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

class DeepSeekProvider(BaseLLMProvider):
    """
    DeepSeek 协议适配器。
    在标准 OpenAI 协议基础上增强了对推理内容的审计。
    """

    def __init__(self, model: str, api_key: str, base_url: str = "https://api.deepseek.com", **kwargs):
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
        """
        全量推理，支持提取 reasoning_content。
        """
        config = config or InferenceConfig()
        payload = self._to_dict_payload(messages, system)
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=payload,
            temperature=config.temperature,
            stream=False,
            **config.extra_params
        )

        choice = response.choices[0]
        message = choice.message
        
        # 提取 DeepSeek 特有的思维链内容
        reasoning = getattr(message, "reasoning_content", None)

        return LLMResponse(
            content=message.content,
            tool_calls=self._parse_tool_calls(message.tool_calls) if message.tool_calls else None,
            model=response.model,
            usage=LLMUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens
            ),
            finish_reason=choice.finish_reason,
            # 将思维链存入 raw 以外的元数据空间（如果 schema 允许扩展，目前存入 raw）
            raw={"original": response, "reasoning": reasoning}
        )

    async def stream(
        self, 
        messages: List[LLMMessage], 
        system: Optional[str] = None, 
        config: Optional[InferenceConfig] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式推理，过滤掉推理内容，仅输出最终回复。
        """
        config = config or InferenceConfig()
        payload = self._to_dict_payload(messages, system)

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=payload,
            stream=True,
            **config.extra_params
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def _to_dict_payload(self, messages: List[LLMMessage], system: Optional[str]) -> List[Dict[str, Any]]:
        """内部转换逻辑。"""
        payload = []
        if system:
            payload.append({"role": "system", "content": system})
        for msg in messages:
            item = {"role": msg.role.value, "content": msg.content}
            if msg.name:
                item["name"] = msg.name
            payload.append(item)
        return payload

    def _parse_tool_calls(self, raw_tool_calls: List[Any]) -> List[ToolCall]:
        """解析工具调用。"""
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
