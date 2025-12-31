import yaml
import os
from typing import Dict, List, Optional
from agents.base_agent import BaseAgent, AgentManifest

from core.skill_manager import skill_manager

class AgentManager:
    """
    Nexus V4 智能体管理与发现中心
    负责管理 Agent 的注册表、生命周期以及根据意图进行调度。
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentManager, cls).__new__(cls)
            cls._instance.registry: Dict[str, AgentManifest] = {}
            cls._instance.active_agents: Dict[str, BaseAgent] = {}
            cls._instance.registry_dir = "agents/registry"
            cls._instance.protocol = ""
            # 初始化时发现技能与清单
            skill_manager.discover_skills()
            cls._instance._load_protocol()
        return cls._instance

    def _load_protocol(self):
        """加载全局运行宪法"""
        library_path = "prompts/library.yaml"
        if os.path.exists(library_path):
            with open(library_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                self.protocol = data.get("protocol", "")

    def discover_registry(self):
        """扫描目录，加载所有 Agent 的 YAML 清单"""
        if not os.path.exists(self.registry_dir):
            os.makedirs(self.registry_dir)
            return

        for filename in os.listdir(self.registry_dir):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                path = os.path.join(self.registry_dir, filename)
                with open(path, "r", encoding="utf-8") as f:
                    try:
                        data = yaml.safe_load(f)
                        manifest = AgentManifest(**data)
                        
                        # 1. 获取技能指令
                        skills_instr = skill_manager.get_skill_instruction(manifest.skills)
                        
                        # 2. 动态合成系统提示词
                        base_prompt = manifest.system_prompt_template or ""
                        manifest.system_prompt_template = f"{base_prompt}\n{skills_instr}\n\n{self.protocol}"
                        
                        self.registry[manifest.agent_id] = manifest
                        print(f"[AgentManager] 已加载并合成智能体: {manifest.name} ({manifest.agent_id})")
                    except Exception as e:
                        print(f"[AgentManager] 加载清单失败 {filename}: {e}")

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """
        获取或唤醒一个智能体实例 (Lazy Loading)
        """
        if agent_id in self.active_agents:
            return self.active_agents[agent_id]

        if agent_id in self.registry:
            manifest = self.registry[agent_id]
            # 动态实例化 Universal Executor (BaseAgent)
            agent = BaseAgent(agent_id=agent_id, manifest=manifest)
            self.active_agents[agent_id] = agent
            print(f"[AgentManager] 智能体已激活并入场: {agent.name}")
            return agent
        
        return None

    def get_all_manifests(self) -> List[AgentManifest]:
        return list(self.registry.values())

agent_manager = AgentManager()
