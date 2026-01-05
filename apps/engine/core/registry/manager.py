import os
from core.registry.agent import AgentRegistry
from core.registry.skill import SkillRegistry

class DiscoveryService:
    """
    资源发现协调服务。
    统一管理智能体与技能的生命周期，实现跨模块的资源检索。
    """
    def __init__(self):
        # 路径解析：自动定位工程根目录下的 agents 文件夹
        current_dir = os.path.dirname(os.path.abspath(__file__))
        engine_root = os.path.dirname(os.path.dirname(current_dir))
        
        self.agents = AgentRegistry(os.path.join(engine_root, "agents", "registry"))
        self.skills = SkillRegistry(os.path.join(engine_root, "agents", "skills"))

    def initialize(self):
        """执行全量扫描与初始化。"""
        self.agents.discover()
        self.skills.discover()

# 全局单例，供系统各组件调用
discovery_service = DiscoveryService()
