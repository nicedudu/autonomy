"""
OpenAI 官方算力供应商实现 (OpenAI Official Provider)

继承自通用 OpenAI 兼容适配器，针对 OpenAI 官方 API 进行特定的默认配置。
"""

from core.llm.providers.openai_compatible import OpenAICompatibleProvider

class OpenAIProvider(OpenAICompatibleProvider):
    """
    OpenAI 官方适配器。
    默认锚定官方 API 端点。
    """
    def __init__(self, model: str, api_key: str, base_url: str = "https://api.openai.com/v1", **kwargs):
        super().__init__(model, api_key, base_url, **kwargs)