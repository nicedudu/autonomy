"""
模型配置解析器 (LLM Config Resolver)

负责从持久化层（Supabase）检索并合成模型服务配置。
实现算力路由与业务逻辑的完全解耦，确保执行单元获取真实、合法的服务凭证。
"""

from typing import Any, Dict, Optional
from services.settings import SettingsService
from core.utils.logging import logger

class LLMConfigResolver:
    """配置解析引擎。"""

    def __init__(self):
        self.settings_service = SettingsService()

    def resolve(self, agent_id: str) -> Dict[str, Any]:
        """
        解析指定智能体对应的模型服务配置。
        
        解析逻辑：
        1. 检索智能体专属调度表 (agents 表)。
        2. 若无专属配置，则回退至系统全局默认配置 (system_settings 表)。
        3. 关联检索供应商详细信息 (llm_providers 表)。
        
        Args:
            agent_id: 智能体标识符。
            
        Returns:
            Dict: 包含 provider_type, api_key, base_url, model 等的配置字典。
        """
        try:
            # 1. 获取系统全量配置快照
            settings = self.settings_service.get_system_settings()
            
            # 2. 尝试匹配智能体专属配置
            agent_configs = settings.get("agent_configs", [])
            target_config = next((ac for ac in agent_configs if ac["identifier"] == agent_id), None)
            
            if target_config:
                provider_info = target_config.get("provider", {})
                return {
                    "provider_type": provider_info.get("type", "openai_compatible"),
                    "api_key": provider_info.get("api_token"),
                    "base_url": provider_info.get("api_base"),
                    "model": target_config.get("model")
                }
            
            # 3. 回退逻辑：使用全局默认配置
            default_provider = settings.get("llm_providers", {})
            return {
                "provider_type": default_provider.get("type", "openai_compatible"),
                "api_key": default_provider.get("api_token"),
                "base_url": default_provider.get("api_base"),
                "model": settings.get("default_model")
            }

        except Exception as e:
            logger.error(f"模型配置解析失败: {str(e)}", agent_id)
            raise RuntimeError(f"无法为智能体 '{agent_id}' 合成模型配置。")

# 全局配置解析单例
config_resolver = LLMConfigResolver()