from typing import Dict, Any
from services.base import BaseService

class SettingsService(BaseService):
    """
    系统全局设置服务。
    """

    def get_system_settings(self) -> Dict[str, Any]:
        """
        加载系统全局默认配置。
        """
        response = self.supabase.table("system_settings").select(
            "*, llm_providers(*)"
        ).eq("id", 1).execute()
        
        if not response.data:
            raise RuntimeError("系统设置未初始化")
        return response.data[0]