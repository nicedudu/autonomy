from typing import Any, Dict

from services.base import BaseService


class AgentService(BaseService):
    """
    智能体配置管理服务。
    """

    def get_agent_config(self, identifier: str) -> Dict[str, Any]:
        """
        获取智能体详情及其关联的 LLM 供应商信息。
        """
        response = self.supabase.table("agents").select(
            "*, llm_providers(*)"
        ).eq("identifier", identifier).execute()

        if not response.data:
            raise RuntimeError(f"未找到智能体: {identifier}")
        return response.data[0]

    def get_prompt_template(self, agent_identifier: str, is_system: bool = True) -> str:
        """
        获取指定智能体的提示词模板内容。
        """
        column = "system_prompt" if is_system else "user_prompt"
        response = self.supabase.table("agents").select(
            column).eq("identifier", agent_identifier).execute()

        if not response.data or not response.data[0].get(column):
            raise RuntimeError(f"未找到智能体提示词模板: {agent_identifier}")
        return response.data[0].get(column)
