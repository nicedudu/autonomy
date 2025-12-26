import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class SupabaseManager:
    """
    Supabase 数据库交互管理器。
    采用单例模式，提供基础的数据读取接口。
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseManager, cls).__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        """
        根据环境变量初始化 Supabase 客户端。
        """
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not url or not key:
            raise EnvironmentError("环境变量缺失: SUPABASE_URL 或 SUPABASE_SERVICE_ROLE_KEY 未配置。")
        
        self.client: Client = create_client(url, key)

    def get_agent_config(self, identifier: str):
        """
        读取智能体详情及关联的供应商信息。

        Args:
            identifier: 智能体标识符。

        Returns:
            Dict or None: 数据库记录对象。
        """
        try:
            response = self.client.table("agents").select("*, llm_providers(*)").eq("identifier", identifier).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"[Supabase] 读取智能体 '{identifier}' 失败: {e}")
            return None

    def get_provider_config(self, provider_id: str):
        """
        获取指定 ID 的供应商配置。

        Args:
            provider_id: 供应商 UUID。

        Returns:
            Dict or None: 数据库记录对象。
        """
        try:
            response = self.client.table("llm_providers").select("*").eq("id", provider_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"[Supabase] 读取供应商 '{provider_id}' 失败: {e}")
            return None