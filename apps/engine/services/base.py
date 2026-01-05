import os
from supabase import Client, create_client

class BaseService:
    """
    数据库服务基类。
    实现 Supabase 客户端的类级别单例共享。
    """
    _client: Client = None

    def __init__(self):
        """初始化服务，确保客户端已连接。"""
        self._ensure_client()

    @classmethod
    def _ensure_client(cls):
        """初始化全局唯一的 Supabase 客户端。"""
        if cls._client is None:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            if not url or not key:
                raise EnvironmentError("Supabase 配置环境变量缺失。")
            cls._client = create_client(url, key)

    @property
    def supabase(self) -> Client:
        """获取数据库客户端实例。"""
        return self._client