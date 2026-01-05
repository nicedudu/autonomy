import os
import yaml
import re
from typing import Dict, List, Optional
from core.schema.models import SkillManifest

class SkillRegistry:
    """
    技能资源注册表。
    遵循 OpenAI Codex 标准，支持 SKILL.md 的元数据索引与指令正文的延迟加载。
    """
    
    def __init__(self, directory: str):
        self._directory = directory
        self._skills: Dict[str, SkillManifest] = {}
        self._instructions: Dict[str, str] = {}

    def discover(self):
        """扫描技能目录，建立元数据索引。"""
        if not os.path.exists(self._directory):
            return

        for root, _, files in os.walk(self._directory):
            if "SKILL.md" in files:
                self._load_skill_file(os.path.join(root, "SKILL.md"))

    def _load_skill_file(self, path: str):
        """解析 SKILL.md (包含 YAML 元数据头与 Markdown 指令正文)。"""
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
                self._skills[skill_id] = skill
                self._instructions[skill_id] = instructions
            except Exception as e:
                print(f"[SkillRegistry] 解析失败 {path}: {e}")

    def get_index_docs(self, skill_ids: List[str]) -> str:
        """生成轻量级索引，用于在 Prompt 中向智能体展示可用能力。"""
        lines = []
        for sid in skill_ids:
            skill = self._skills.get(sid)
            if skill:
                lines.append(f"- `{sid}`: {skill.description}")
        return "\n".join(lines) if lines else "无可用技能"

    def get_instruction(self, skill_id: str) -> str:
        """获取完整的 Markdown 执行指南。"""
        return self._instructions.get(skill_id, "")

    def all(self) -> Dict[str, SkillManifest]:
        """返回所有已索引的技能。"""
        return self._skills
