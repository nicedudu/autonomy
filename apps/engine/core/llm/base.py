"""
LLM 供应商抽象基座 (LLM Provider Base Specification)

本模块定义了模型适配器的标准化接口，采用适配器模式（Adapter Pattern）屏蔽底层不同推理引擎的差异。
职责：强制执行统一的推理行为契约，不持有任何特定厂商的协议实现细节。
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Optional

from .schema import LLMMessage, LLMResponse, InferenceConfig

class BaseLLMProvider(ABC):
    """
    LLM 供应商抽象基类。
    
    定义了算力供应商必须遵守的接口标准。
    具体的协议转换（如 LLMMessage 转换为厂商私有格式）应由子类实现私有处理。
    """

    def __init__(self, model: str, api_key: str, base_url: str, **kwargs):
        """
        初始化供应商基础配置。
        """
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.client_options = kwargs

    @abstractmethod
    async def generate(
        self, 
        messages: List[LLMMessage], 
        system: Optional[str] = None, 
        config: Optional[InferenceConfig] = None
    ) -> LLMResponse:
        """
        异步全量推理接口。
        
        Args:
            messages: 标准化消息序列。
            system: 可选的系统级全局指令。
            config: 推理采样配置。
            
        Returns:
            LLMResponse: 归一化后的响应结果。
        """
        pass

    @abstractmethod
    async def stream(
        self, 
        messages: List[LLMMessage], 
        system: Optional[str] = None, 
        config: Optional[InferenceConfig] = None
    ) -> AsyncGenerator[str, None]:
        """
        异步流式推理接口。
        
        通过生成器实时吐出增量文本内容。
        """
        yield ""