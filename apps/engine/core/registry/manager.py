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
        # 1. 初始化智能体 (V2.0 逻辑)
        self.agents.discover()
        
        # 2. 注册核心工具
        from tools import CORE_TOOLS
        from core.tools.registry import tool_registry
        from core.tools.base import BaseTool
        
        for t in CORE_TOOLS:
            # 兼容处理：确保拿到的是 BaseTool 实例
            if isinstance(t, BaseTool):
                tool_registry.register(t)
            elif hasattr(t, "name"):
                # 如果是其他具有 name 属性的对象
                tool_registry.register(t)
            else:
                print(f"\033[91m[Discovery] Skipping invalid tool: {t}\033[0m")
        
        # 3. 扫描外部技能 (未来可扩展)
        self.skills.discover()

# 全局单例，供系统各组件调用
discovery_service = DiscoveryService()
