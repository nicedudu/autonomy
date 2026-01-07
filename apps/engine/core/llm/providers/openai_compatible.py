from typing import AsyncGenerator, List, Dict, Any, Optional
from openai import AsyncOpenAI
from ..base import BaseLLMProvider
from ..schema import LLMMessage, LLMResponse, LLMUsage, LLMRole

class OpenAICompatibleProvider(BaseLLMProvider):
    """OpenAI 标准兼容协议适配器。"""

    def __init__(self, api_key: str, base_url: str, **kwargs):
        super().__init__(api_key, base_url, **kwargs)
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=120.0)

    def _to_native_messages(self, messages: List[LLMMessage], system: Optional[str] = None) -> List[Dict[str, str]]:
        """执行专业级角色映射。
        
        将自定义协议中的 TOOL 角色映射为 USER 角色的环境观测反馈，
        以规避供应商对原生 Function Calling ID 的强制性闭环校验。
        """
        native_msgs = []
        
        if system:
            native_msgs.append({"role": "system", "content": system})
            
        for m in messages:
            if m.role == LLMRole.TOOL:
                # 转换为带标识的观测反馈，确保模型能区分用户指令与执行结果
                label = f"[{m.name}] " if m.name else ""
                content = f"观测值 {label}: {m.content}"
                native_msgs.append({"role": "user", "content": content})
            else:
                native_msgs.append({"role": m.role.value, "content": m.content})
                
        return native_msgs

    async def generate(self, messages: List[LLMMessage], system: Optional[str] = None, timeout: float = 60.0, **kwargs) -> LLMResponse:
        model = kwargs.pop("model", self.config.get("model"))
        if not model:
            raise ValueError(f"{self.__class__.__name__} 缺失 model 参数")
        
        res = await self.client.chat.completions.create(
            model=model,
            messages=self._to_native_messages(messages, system),
            stream=False,
            timeout=timeout,
            **kwargs
        )
        choice = res.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            model=res.model,
            usage=LLMUsage(**res.usage.model_dump()),
            finish_reason=choice.finish_reason,
            raw=res
        )

    async def stream(self, messages: List[LLMMessage], system: Optional[str] = None, timeout: float = 60.0, **kwargs) -> AsyncGenerator[str, None]:
        model = kwargs.pop("model", self.config.get("model"))
        if not model:
            raise ValueError(f"{self.__class__.__name__} 缺失 model 参数")
        
        res = await self.client.chat.completions.create(
            model=model,
            messages=self._to_native_messages(messages, system),
            stream=True,
            timeout=timeout,
            **kwargs
        )
        async for chunk in res:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content