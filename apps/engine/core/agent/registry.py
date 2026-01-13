"""
智能体注册中心 (Agent Registry Specification)

本模块作为系统能力的发现层，负责智能体包的物理寻址、环境隔离加载及规格内省。
AgentRegistry 实现了“定义即服务”的发现模式，确保智能体规格（Profile）的动态交付与契约校验。
"""

import os
import sys
import importlib.util
from pathlib import Path
from typing import Optional, List, Dict
from dotenv import load_dotenv

from core.agent.profile import AgentProfile

class AgentRegistry:
    """
    智能体全生命周期发现与路由中心。
    """

    def __init__(self, agents_root: str = "agents"):
        # 锚定智能体包存放的物理根目录
        self.root_path = Path(agents_root).resolve()
        # 运行时规格缓存，避免重复执行内省逻辑
        self._cache: Dict[str, AgentProfile] = {}

    def get_profile(self, agent_id: str) -> Optional[AgentProfile]:
        """
        检索并动态加载指定智能体的规格定义。
        
        执行逻辑:
        1. 命中缓存直接返回。
        2. 物理寻址:定位 agents/{agent_id}/agent.py。
        3. 环境隔离:注入该智能体包内的私有 .env 配置。
        4. 契约加载:执行模块并提取导出的 'profile' 实例。
        """
        if agent_id in self._cache:
            return self._cache[agent_id]

        agent_dir = self.root_path / agent_id
        entry_file = agent_dir / "agent.py"

        if not agent_dir.exists() or not entry_file.exists():
            return None

        # 1. 注入私有环境变量 (隔离审计)
        env_file = agent_dir / ".env"
        if env_file.exists():
            load_dotenv(dotenv_path=env_file, override=True)

        # 2. 动态模块内省
        try:
            module_name = f"agents.{agent_id}.entry"
            spec = importlib.util.spec_from_file_location(module_name, str(entry_file))
            if not spec or not spec.loader:
                return None

            module = importlib.util.module_from_spec(spec)
            
            # 临时注入搜索路径，支持包内相对导入逻辑
            sys.path.insert(0, str(agent_dir))
            try:
                spec.loader.exec_module(module)
                # 契约校验:强制要求导出 profile 变量
                profile = getattr(module, "profile", None)
                if isinstance(profile, AgentProfile):
                    self._cache[agent_id] = profile
                    return profile
            finally:
                if str(agent_dir) in sys.path:
                    sys.path.remove(str(agent_dir))
        except Exception:
            # 异常处理:寻址或内省失败均返回空，由编排层处理缺失逻辑
            return None
        
        return None

    def get_agents(self) -> List[str]:
        """
        探测物理目录，列出所有合规的智能体标识符。
        """
        if not self.root_path.exists():
            return []
        
        return [
            d.name for d in self.root_path.iterdir() 
            if d.is_dir() and (d / "agent.py").exists()
        ]

# 导出全局注册中心单例 (系统算力发现的唯一入口)
agent_registry = AgentRegistry()
