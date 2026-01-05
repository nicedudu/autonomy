from typing import Dict, Any
from services.base import BaseService

class LLMProviderService(BaseService):
    """
    大模型供应商配置服务。
    """

    def get_provider_config(self, provider_id: str) -> Dict[str, Any]:
        """
        获取指定 ID 的供应商配置信息。
        """
        response = self.supabase.table("llm_providers").select("*").eq("id", provider_id).execute()
        if not response.data:
            raise RuntimeError(f"未找到供应商配置: {provider_id}")
        return response.data[0]