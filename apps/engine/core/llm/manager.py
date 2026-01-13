"""
LLM 算力调度中心 (LLM Orchestration Manager)
"""

from typing import Dict, Type, List, Any, Optional
from core.llm.base import BaseLLMProvider
from core.llm.providers.openai import OpenAIProvider
from core.llm.providers.anthropic import AnthropicProvider
from core.llm.providers.deepseek import DeepSeekProvider
from core.llm.providers.openai_compatible import OpenAICompatibleProvider
from core.llm.schema import LLMProviderConfig

class LLMManager:
    """
    模型算力管理器。
    """

    def __init__(self):
        self._registry: Dict[str, Type[BaseLLMProvider]] = {
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "deepseek": DeepSeekProvider,
            "openai_compatible": OpenAICompatibleProvider
        }

    def create_client(self, config: LLMProviderConfig) -> BaseLLMProvider:
        """
        算力客户端工厂方法：直接从配置模型实例化。
        """
        if config.provider_type not in self._registry:
            raise ValueError(f"算力路由失败: 供应商类型 '{config.provider_type}' 未定义。")

        ProviderClass = self._registry[config.provider_type]
        
        return ProviderClass(
            model=config.model,
            api_key=config.api_key,
            base_url=config.base_url,
            **config.extra_options
        )

# 全局单例
llm_manager = LLMManager()
