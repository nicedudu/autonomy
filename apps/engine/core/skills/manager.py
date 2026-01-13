import os
import yaml
import re
from typing import Dict, List, Optional
from core.skills.base import Skill

class SkillManager:
    """
    技能管理器。
    负责从 'skills/' 目录加载 SKILL.md 定义。
    """
    def __init__(self, skills_dir: str):
        self.skills_dir = skills_dir
        self._skills: Dict[str, Skill] = {}

    def discover(self):
        """扫描独立技能目录"""
        if not os.path.exists(self.skills_dir):
            return

        for skill_folder in os.listdir(self.skills_dir):
            folder_path = os.path.join(self.skills_dir, skill_folder)
            if not os.path.isdir(folder_path):
                continue
            
            skill_md_path = os.path.join(folder_path, "SKILL.md")
            if os.path.exists(skill_md_path):
                skill = self._load_skill_from_md(skill_md_path, skill_id=skill_folder)
                if skill:
                    self._skills[skill.skill_id] = skill

    def _load_skill_from_md(self, file_path: str, skill_id: str) -> Optional[Skill]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            header_match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if not header_match:
                return None

            header_yaml = header_match.group(1)
            metadata = yaml.safe_load(header_yaml)
            instructions = content[header_match.end():].strip()

            return Skill(
                skill_id=skill_id,
                name=metadata.get("name", skill_id),
                description=metadata.get("description", ""),
                instructions=instructions,
                tool_names=metadata.get("tools", []),
                metadata=metadata
            )
        except Exception:
            return None

    def get_skill(self, skill_id: str) -> Optional[Skill]:
        return self._skills.get(skill_id)

    def list_skills(self) -> List[Skill]:
        return list(self._skills.values())