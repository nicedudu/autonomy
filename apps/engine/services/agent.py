from typing import Dict, Any, Optional
from services.base import BaseService

class AgentService(BaseService):
    """
    智能体业务服务。
    负责处理 Agent 相关的持久化数据检索与状态管理。
    """

    def get_agent_config(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        从数据库检索指定智能体的算力配置。
        
        关联检索：agents 表与 llm_providers 表进行 Inner Join。
        """
        response = self.supabase.table("agents").select(
            "*, llm_providers(*)"
        ).eq("identifier", agent_id).execute()
        
        return response.data[0] if response.data else None