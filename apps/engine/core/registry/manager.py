import os
import yaml
import re
from typing import Dict, Generic, Type, TypeVar, List, Optional
from pydantic import BaseModel
from core.schema.models import AgentManifest, SkillManifest

T = TypeVar("T", bound=BaseModel)

class Registry(Generic[T]):
    """具备渐进式披露能力的资源注册中心。"""
    
    def __init__(self, resource_type: Type[T], directory: str):
        self._resource_type = resource_type
        self._directory = directory
        self._storage: Dict[str, T] = {}
        # 存储技能的完整 Markdown 指令
        self._instructions: Dict[str, str] = {}

    def discover(self):
        """扫描目录并发现资源。"""
        if not os.path.exists(self._directory):
            return

        for root, dirs, files in os.walk(self._directory):
            # 支持目录结构（如 skills/ecom/SKILL.md）
            if "SKILL.md" in files:
                self._load_skill_directory(os.path.join(root, "SKILL.md"))
            else:
                # 兼容旧的单一 YAML 文件结构
                for file in files:
                    if file.endswith((".yaml", ".yml")):
                        self._load_resource(os.path.join(root, file))

    def _load_skill_directory(self, path: str):
        """
        解析符合 OpenAI Codex 标准的 SKILL.md 文件。
        规范：YAML 前置元数据 + Markdown 指令正文。
        使用目录名作为 Skill ID。
        """
        skill_id = os.path.basename(os.path.dirname(path))
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            
        match = re.match(r"^---(.*?)---(.*)$", content, re.DOTALL)
        if match:
            yaml_str = match.group(1).strip()
            instructions = match.group(2).strip()
            try:
                data = yaml.safe_load(yaml_str)
                skill = SkillManifest(**data)
                skill.instructions = instructions
                
                self._storage[skill_id] = skill
                self._instructions[skill_id] = instructions
            except Exception as e:
                print(f"[Registry] 解析标准 SKILL.md 失败 {path}: {e}")

    def _load_resource(self, path: str):
        """加载传统的单一清单文件。"""
        with open(path, "r", encoding="utf-8") as f:
            try:
                data = yaml.safe_load(f)
                resource = self._resource_type(**data)
                
                # 针对 Agent 的特殊逻辑：应用数据库覆盖
                if isinstance(resource, AgentManifest):
                    resource = self._apply_database_override(resource)
                
                resource_id = getattr(resource, "agent_id", None) or \
                              getattr(resource, "skill_id", None)
                if resource_id:
                    self._storage[resource_id] = resource
            except Exception as e:
                print(f"[Registry] 加载失败 {path}: {e}")

    def _apply_database_override(self, manifest: AgentManifest) -> AgentManifest:
        """数据库配置覆盖逻辑。"""
        from core.supabase_manager import SupabaseManager
        db = SupabaseManager()
        db_config = db.get_agent_config(manifest.agent_id)
        if db_config:
            manifest.name = db_config.get("name", manifest.name)
            if not manifest.model:
                manifest.model = db_config.get("model")
        return manifest

    def get(self, resource_id: str) -> Optional[T]:
        return self._storage.get(resource_id)

    def get_instruction(self, skill_id: str) -> str:
        """获取技能的完整执行指令。"""
        return self._instructions.get(skill_id, "")

    def get_index_docs(self, skill_ids: List[str]) -> str:
        """生成轻量级的技能索引文档。"""
        lines = []
        for sid in skill_ids:
            skill = self._storage.get(sid)
            if skill:
                lines.append(f"- `{skill.skill_id}`: {skill.description}")
        return "\n".join(lines) if lines else "无"

    def all(self) -> Dict[str, T]:
        return self._storage

class DiscoveryService:
    """中心化发现服务。"""
    def __init__(self):
        self.agents = Registry(AgentManifest, "agents/registry")
        self.skills = Registry(SkillManifest, "agents/skills")

    def initialize(self):
        self.agents.discover()
        self.skills.discover()

discovery_service = DiscoveryService()
