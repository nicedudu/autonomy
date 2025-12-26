import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class SupabaseManager:
    """
    Supabase 管理器：负责与云端数据库进行通信。
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseManager, cls).__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") # 建议在Engine端使用Service Role Key以获得更高效的读取权限
        
        if not url or not key:
            print("[SupabaseManager] WARNING: SUPABASE_URL or KEY is missing. Agent will use local config fallback.")
            self.client = None
        else:
            self.client: Client = create_client(url, key)
            print(f"[SupabaseManager] Connected to: {url}")

    def get_agent_config(self, agent_id: str):
        """从 agents 表中获取指定 Agent 的实时配置"""
        if not self.client:
            return None
        
        try:
            response = self.client.table("agents").select("*").eq("agent_id", agent_id).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            print(f"[SupabaseManager] Error fetching config for {agent_id}: {e}")
            return None

    def get_provider_config(self, provider_name: str):
        """获取模型供应商的默认全局配置"""
        if not self.client:
            return None
        try:
            response = self.client.table("llm_providers").select("*").ilike("name", provider_name).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"[SupabaseManager] Error fetching provider {provider_name}: {e}")
            return None
        except Exception as e:
            print(f"[SupabaseManager] Error fetching config for {agent_id}: {e}")
            return None

    def get_prompt_template(self, slug: str):
        """获取指定的 Prompt 模板内容"""
        if not self.client:
            return None
        try:
            response = self.client.table("prompt_library").select("template").eq("slug", slug).execute()
            if response.data:
                return response.data[0]["template"]
            return None
        except Exception as e:
            print(f"[SupabaseManager] Error fetching prompt {slug}: {e}")
            return None
