"""
算力配置解析器 (LLM Config Resolver)

职责：通过协调 AgentService 与 SettingsService，实现分层算力路由解析。
"""

from core.llm.schema import LLMProviderConfig
from core.utils.logging import logger

class LLMConfigResolver:
    """
    配置解析引擎。
    """

    def __init__(self):
        # 采用延迟加载，确保服务实例化的领域隔离
        self._agent_service = None
        self._settings_service = None

    @property
    def agent_service(self):
        if self._agent_service is None:
            from services.agent import AgentService
            self._agent_service = AgentService()
        return self._agent_service

    @property
    def settings_service(self):
        if self._settings_service is None:
            from services.settings import SettingsService
            self._settings_service = SettingsService()
        return self._settings_service

    def resolve(self, agent_id: str) -> LLMProviderConfig:
        """
        解析逻辑：
        1. [AgentService] 获取专属配置。
        2. [SettingsService] 若无专属配置，则获取系统默认配置。
        """
        try:
            # 优先检查 Agent 专属大脑
            agent_data = self.agent_service.get_agent_config(agent_id)
            
            if agent_data and agent_data.get("llm_providers"):
                p = agent_data["llm_providers"]
                return LLMProviderConfig(
                    provider_type=p.get("type"),
                    model=agent_data.get("model"),
                    api_key=p.get("api_token", ""),
                    base_url=p.get("api_base"),
                    extra_options=p.get("extra_config", {})
                )
            
            # 兜底：使用全局配置
            system_settings = self.settings_service.get_system_settings()
            default_p = system_settings.get("llm_providers")
            
            return LLMProviderConfig(
                provider_type=default_p.get("type"),
                model=system_settings.get("default_model"),
                api_key=default_p.get("api_token", ""),
                base_url=default_p.get("api_base")
            )

        except Exception as e:
            logger.error(f"LLM 路由解析崩溃 [{agent_id}]: {e}")
            raise RuntimeError(f"未能为智能体 '{agent_id}' 解析到有效的算力路径。")

# 导出单例
config_resolver = LLMConfigResolver()
