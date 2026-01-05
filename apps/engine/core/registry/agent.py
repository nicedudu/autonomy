import os
import yaml
from typing import Dict, Optional
from core.schema.models import AgentManifest

class AgentRegistry:
    """
    智能体配置注册表。
    处理 YAML 定义文件的加载、验证以及数据库运行时配置的实时覆盖。
    """
    
    def __init__(self, directory: str):
        self._directory = directory
        self._agents: Dict[str, AgentManifest] = {}

    def discover(self):
        """扫描指定目录并加载所有智能体定义。"""
        if not os.path.exists(self._directory):
            return

        for root, _, files in os.walk(self._directory):
            for file in files:
                if file.endswith((".yaml", ".yml")):
                    self._load_agent(os.path.join(root, file))

    def _load_agent(self, path: str):
        """解析单个智能体 YAML 文件。"""
        with open(path, "r", encoding="utf-8") as f:
            try:
                data = yaml.safe_load(f)
                agent = AgentManifest(**data)
                agent = self._apply_database_override(agent)
                self._agents[agent.agent_id] = agent
            except Exception as e:
                print(f"[AgentRegistry] 加载失败 {path}: {e}")

    def _apply_database_override(self, manifest: AgentManifest) -> AgentManifest:
        """应用来自数据库的配置覆盖，确保管理后台的修改实时生效。"""
        try:
            from services.agent import AgentService
            svc = AgentService()
            db_config = svc.get_agent_config(manifest.agent_id)
            if db_config:
                manifest.name = db_config.get("name", manifest.name)
                if not manifest.model:
                    manifest.model = db_config.get("model")
        except Exception:
            pass
        return manifest

    def get(self, agent_id: str) -> Optional[AgentManifest]:
        """获取指定 ID 的智能体元数据。"""
        return self._agents.get(agent_id)

    def all(self) -> Dict[str, AgentManifest]:
        """返回当前已加载的所有智能体。"""
        return self._agents
