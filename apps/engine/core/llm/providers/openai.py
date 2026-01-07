from typing import AsyncGenerator, List, Dict, Any, Optional
from openai import AsyncOpenAI
from ..base import BaseLLMProvider
from ..schema import LLMMessage, LLMResponse, LLMUsage, LLMRole

class OpenAIProvider(BaseLLMProvider):
    """OpenAI 官方原生协议适配器。"""

    def __init__(self, api_key: str, base_url: str, **kwargs):
        super().__init__(api_key, base_url, **kwargs)
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=120.0)

    def _to_native_messages(self, messages: List[LLMMessage], system: Optional[str] = None) -> List[Dict[str, Any]]:
        """实现官方协议下的 Function Calling 模拟映射。"""
        native_msgs = []
        if system:
            native_msgs.append({"role": "system", "content": system})
            
        for m in messages:
            if m.role == LLMRole.TOOL:
                native_msgs.append({
                    "role": "tool",
                    "content": m.content,
                    "tool_call_id": m.tool_call_id
                })
            elif m.role == LLMRole.ASSISTANT:
                msg_body = {"role": "assistant", "content": m.content}
                if m.is_tool_request and m.tool_call_id:
                    msg_body["tool_calls"] = [{
                        "id": m.tool_call_id,
                        "type": "function",
                        "function": {"name": m.name or "execute", "arguments": "{}"}
                    }]
                native_msgs.append(msg_body)
            else:
                native_msgs.append({"role": m.role.value, "content": m.content})
        return native_msgs

    async def generate(self, messages: List[LLMMessage], system: Optional[str] = None, timeout: float = 60.0, **kwargs) -> LLMResponse:
        model = kwargs.pop("model", self.config.get("model"))
        if not model:
            raise ValueError(f"{self.__class__.__name__} 缺失 model 参数")
        
        response = await self.client.chat.completions.create(
            model=model,
            messages=self._to_native_messages(messages, system),
            stream=False,
            timeout=timeout,
            **kwargs
        )
        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            usage=LLMUsage(**response.usage.model_dump()),
            finish_reason=choice.finish_reason,
            raw=response
        )

    async def stream(self, messages: List[LLMMessage], system: Optional[str] = None, timeout: float = 60.0, **kwargs) -> AsyncGenerator[str, None]:
        model = kwargs.pop("model", self.config.get("model"))
        if not model:
            raise ValueError(f"{self.__class__.__name__} 缺失 model 参数")
        
        response = await self.client.chat.completions.create(
            model=model,
            messages=self._to_native_messages(messages, system),
            stream=True,
            timeout=timeout,
            **kwargs
        )
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
