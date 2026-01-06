from typing import Any, Dict, Optional
from core.schema.models import AgentManifest, LLMConfig
from services.settings import SettingsService
from services.agent import AgentService

class LLMConfigResolver:
    """
    DB 驱动型配置解析器。
    严格执行：所有模型、供应商和运行参数均来源于数据库。
    """

    def __init__(self):
        self.settings_svc = SettingsService()
        self.agent_svc = AgentService()

    def resolve(self, agent_id: str) -> LLMConfig:
        """
        合成 LLM 配置。
        - 路由 (Provider/Model): 来源于数据库。
        - 逻辑 (Temp/MaxTokens): 来源于代码定义。
        """
        # 1. 获取代码中的静态定义 (Soul)
        from core.registry.internal import get_agent_definition
        definition = get_agent_definition(agent_id)
        if not definition:
            raise ValueError(f"Agent '{agent_id}' is not defined in code.")

        # 2. 获取全局系统设置 (兜底路由)
        sys_settings = self.settings_svc.get_system_settings()
        
        # 3. 获取 Admin 路由覆盖
        db_agent_config = {}
        try:
            db_agent_config = self.agent_svc.get_agent_config(agent_id)
        except Exception:
            pass

        # 4. 确定供应商 (Admin 权限)
        provider_data = db_agent_config.get("llm_providers") or sys_settings.get("llm_providers")
        if isinstance(provider_data, list) and len(provider_data) > 0:
            provider_data = provider_data[0]
        
        if not provider_data:
            raise RuntimeError(f"Admin has not assigned any provider for Agent '{agent_id}'.")

        # 5. 确定模型 (Admin 权限)
        model = db_agent_config.get("model") or sys_settings.get("default_model")

        # 6. 合成配置 (融合路由与逻辑)
        return LLMConfig(
            provider=(provider_data.get("type") or "openai_compatible").lower(),
            api_key=provider_data.get("api_token"),
            base_url=provider_data.get("api_base"),
            model=model,
            temperature=definition.temperature, # 来源于代码
            max_tokens=definition.max_tokens    # 来源于代码
        )
