from typing import AsyncGenerator, List, Dict, Any, Optional
from anthropic import AsyncAnthropic
from ..base import BaseLLMProvider
from ..schema import LLMMessage, LLMResponse, LLMUsage, LLMRole

class AnthropicProvider(BaseLLMProvider):
    """Anthropic Messages API 协议适配器。"""

    def __init__(self, api_key: str, base_url: str, **kwargs):
        super().__init__(api_key, base_url, **kwargs)
        self.client = AsyncAnthropic(api_key=api_key, base_url=base_url)

    def _prepare_payload(self, messages: List[LLMMessage], system: Optional[str] = None) -> Dict[str, Any]:
        """准备 Anthropic 原生载荷，合并系统提示词。"""
        system_content = system or ""
        native_msgs = []
        
        for m in messages:
            if m.role == LLMRole.SYSTEM:
                system_content += "\n" + m.content
            else:
                role = "assistant" if m.role in [LLMRole.ASSISTANT, LLMRole.TOOL] else "user"
                if native_msgs and native_msgs[-1]["role"] == role:
                    native_msgs[-1]["content"] += "\n\n" + m.content
                else:
                    native_msgs.append({"role": role, "content": m.content})
        
        return {
            "system": system_content.strip() if system_content else None,
            "messages": native_msgs
        }

    async def generate(self, messages: List[LLMMessage], system: Optional[str] = None, **kwargs) -> LLMResponse:
        model = kwargs.pop("model", self.config.get("model"))
        if not model:
            raise ValueError(f"{self.__class__.__name__} 缺失 model 参数")
            
        payload = self._prepare_payload(messages, system)
        response = await self.client.messages.create(
            model=model,
            max_tokens=kwargs.pop("max_tokens", 4096),
            stream=False,
            **payload,
            **kwargs
        )

        content = "".join([block.text for block in response.content if hasattr(block, "text")])
        
        return LLMResponse(
            content=content,
            model=response.model,
            usage=LLMUsage(
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
                total_tokens=response.usage.input_tokens + response.usage.output_tokens
            ),
            finish_reason=response.stop_reason,
            raw=response
        )

    async def stream(self, messages: List[LLMMessage], system: Optional[str] = None, **kwargs) -> AsyncGenerator[str, None]:
        model = kwargs.pop("model", self.config.get("model"))
        if not model:
            raise ValueError(f"{self.__class__.__name__} 缺失 model 参数")
            
        payload = self._prepare_payload(messages, system)
        async with self.client.messages.stream(
            model=model,
            max_tokens=kwargs.pop("max_tokens", 4096),
            **payload,
            **kwargs
        ) as stream:
            async for text in stream.text_stream:
                yield text