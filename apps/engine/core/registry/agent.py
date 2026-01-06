from typing import Dict, Optional

from core.registry.internal import INTERNAL_AGENTS
from core.schema.models import AgentManifest


class AgentRegistry:
    """
    智能体配置注册表。
    不再依赖物理文件，而是通过代码内置定义。
    """

    def __init__(self, directory: str = None):
        # 兼容性保留 directory 参数，但不再执行物理扫描
        self._agents: Dict[str, AgentManifest] = {}
        self._initialize()

    def _initialize(self):
        """将内置定义转换为清单模型。"""
        for agent_id, definition in INTERNAL_AGENTS.items():
            self._agents[agent_id] = AgentManifest(
                agent_id=definition.agent_id,
                name=definition.name,
                role=definition.role,
                capabilities=definition.capabilities
            )

    def discover(self):
        """扫描方法现在是静默的，因为数据已在初始化时加载。"""
        pass

    def get(self, agent_id: str) -> Optional[AgentManifest]:
        """获取指定 ID 的智能体元数据。"""
        return self._agents.get(agent_id)

    def all(self) -> Dict[str, AgentManifest]:
        """返回所有内置智能体。"""
        return self._agents
