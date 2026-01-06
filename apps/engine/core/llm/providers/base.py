from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, List, Any, Optional
from pydantic import BaseModel, Field

class ProviderUsage(BaseModel):
    """用量统计。"""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

class ProviderResponse(BaseModel):
    """标准响应对象。"""
    id: str
    model: str
    status: str
    output: List[Dict[str, Any]] = Field(default_factory=list)
    usage: ProviderUsage = Field(default_factory=ProviderUsage)

class LLMProviderAdapter(ABC):
    """协议适配器基类。"""
    
    @abstractmethod
    async def stream(
        self, 
        model: str, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """异步流式输出。"""
        pass

    @abstractmethod
    def call(
        self, 
        model: str, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> ProviderResponse:
        """同步阻塞调用。"""
        pass