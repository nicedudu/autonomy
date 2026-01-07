from typing import Dict, Type, List
from .base import BaseLLMProvider
from .providers.openai import OpenAIProvider
from .providers.anthropic import AnthropicProvider
from .providers.openai_compatible import OpenAICompatibleProvider

class LLMProviderManager:
    """模型服务管理器。
    
    采用工厂模式与注册表模式，管理供应商适配器并负责客户端实例的动态生命周期调度。
    """

    def __init__(self):
        self._registry: Dict[str, Type[BaseLLMProvider]] = {
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "openai_compatible": OpenAICompatibleProvider
        }

    def register_provider(self, provider_type: str, provider_cls: Type[BaseLLMProvider]):
        """动态注册第三方或自定义模型适配器。"""
        self._registry[provider_type] = provider_cls

    def get_supported_types(self) -> List[str]:
        """返回已注册的供应商协议标识列表。"""
        return list(self._registry.keys())

    def create_client(
        self, 
        provider_type: str, 
        api_key: str, 
        base_url: str, 
        **kwargs
    ) -> BaseLLMProvider:
        """模型客户端工厂方法。
        
        Args:
            provider_type: 供应商标识。
            api_key: 模型服务凭证。
            base_url: API 入口地址。
            **kwargs: 推理参数配置。
            
        Returns:
            BaseLLMProvider: 标准化客户端实例。
            
        Raises:
            ValueError: 供应商类型未注册。
        """
        if provider_type not in self._registry:
            raise ValueError(f"未注册的供应商类型: '{provider_type}'")

        provider_cls = self._registry[provider_type]
        return provider_cls(api_key=api_key, base_url=base_url, **kwargs)

llm_manager = LLMProviderManager()
