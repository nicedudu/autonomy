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
        """
        response = self.client.table("agents").select("*, llm_providers(*)").eq("identifier", identifier).execute()
        if not response.data:
            raise RuntimeError(f"数据库中未找到智能体标识符: '{identifier}'")
        return response.data[0]

    def get_provider_config(self, provider_id: str):
        """
        获取指定 ID 的供应商配置。
        """
        response = self.client.table("llm_providers").select("*").eq("id", provider_id).execute()
        if not response.data:
            raise RuntimeError(f"数据库中未找到供应商 ID: '{provider_id}'")
        return response.data[0]

    def get_system_settings(self):
        """
        获取系统全局设置。
        """
        response = self.client.table("system_settings").select("*, llm_providers(*)").eq("id", 1).execute()
        if not response.data:
            raise RuntimeError("数据库中未初始化 system_settings 表数据 (ID: 1)")
        return response.data[0]

    def get_prompt_template(self, slug: str) -> str:
        """
        获取提示词模板。
        """
        parts = slug.split('_')
        if len(parts) < 2:
            raise ValueError(f"无效的 Prompt Slug 格式: '{slug}'，预期格式如 'ceo_system'")
            
        agent_type = parts[0]
        prompt_type = parts[1] # system or user
        
        identifier = f"{agent_type}_agent"
        column = "system_prompt" if prompt_type == "system" else "user_prompt"
        
        response = self.client.table("agents").select(column).eq("identifier", identifier).execute()
        if not response.data or not response.data[0].get(column):
            raise RuntimeError(f"未找到智能体 '{identifier}' 的 {column}")
        return response.data[0].get(column)