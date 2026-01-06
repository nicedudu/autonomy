import hashlib
from typing import Any, Dict

from core.llm.providers.anthropic import AnthropicAdapter
from core.llm.providers.base import LLMProviderAdapter
from core.llm.providers.openai import OpenAIAdapter
from core.llm.providers.openai_compatible import OpenAICompatibleAdapter


class LLMClientManager:
    """
    协议驱动生命周期管理器 (LLM Factory)。
    负责根据配置生产并缓存对应的 LLM 适配器实例。
    """

    def __init__(self):
        self._adapters: Dict[str, LLMProviderAdapter] = {}

    def get_adapter(self, config: Dict[str, Any]) -> LLMProviderAdapter:
        """根据供应商类型分发对应的适配器实例。"""
        raw_key = f"{config.get('provider_type')}_{config.get('base_url')}_{config.get('api_key')}"
        cache_key = hashlib.md5(raw_key.encode('utf-8')).hexdigest()

        if cache_key not in self._adapters:
            ptype = config.get("provider_type", "openai_compatible")
            api_key = config.get("api_key")
            base_url = config.get("base_url")

            adapter = self._create_adapter(ptype, api_key, base_url)
            self._adapters[cache_key] = adapter

        return self._adapters[cache_key]

    def _create_adapter(self, ptype: str, api_key: str, base_url: str) -> LLMProviderAdapter:
        """工厂方法：创建具体的适配器实例。"""
        import os

        # 容错处理：如果 api_key 为空，尝试从环境变量获取
        if not api_key:
            if ptype == "openai":
                api_key = os.environ.get("OPENAI_API_KEY")
            elif ptype == "anthropic":
                api_key = os.environ.get("ANTHROPIC_API_KEY")

            # 如果依然为空且是兼容模式，注入占位符（兼容本地模型）
            if not api_key and ptype not in ["openai", "anthropic"]:
                api_key = "sk-no-key-required"

        if ptype == "openai":
            return OpenAIAdapter(api_key, base_url)
        elif ptype == "anthropic":
            return AnthropicAdapter(api_key, base_url)
        else:
            return OpenAICompatibleAdapter(api_key, base_url)
