import asyncio
from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Optional
from .schema import LLMMessage, LLMResponse

class BaseLLMProvider(ABC):
    """LLM 供应商抽象基类。
    
    确立供应商适配器的标准化接口契约。
    """

    def __init__(self, api_key: str, base_url: str, **kwargs):
        self.api_key = api_key
        self.base_url = base_url
        self.config = kwargs

    @abstractmethod
    async def generate(
        self, 
        messages: List[LLMMessage], 
        system: Optional[str] = None, 
        **kwargs
    ) -> LLMResponse:
        """执行异步全量推理。
        
        Args:
            messages: 符合协议的消息序列。
            system: 可选的系统级指令（System Prompt）。
            **kwargs: 动态推理参数。
            
        Returns:
            LLMResponse: 标准响应对象。
        """
        pass

    @abstractmethod
    async def stream(
        self, 
        messages: List[LLMMessage], 
        system: Optional[str] = None, 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """执行异步流式推理。
        """
        pass

    def generate_sync(self, messages: List[LLMMessage], system: Optional[str] = None, **kwargs) -> LLMResponse:
        """全量推理的同步包装器。"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.generate(messages, system=system, **kwargs))