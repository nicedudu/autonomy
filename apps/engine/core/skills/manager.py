import os
import yaml
import re
from typing import Dict, List, Optional
from core.skills.base import Skill

class SkillManager:
    """
    技能管理器。
    负责从文件系统加载技能并提供查询接口。
    """
    def __init__(self, skills_dir: str):
        self.skills_dir = skills_dir
        self._skills: Dict[str, Skill] = {}

    def discover(self):
        """扫描目录并加载所有有效的 SKILL.md"""
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
        """解析 SKILL.md 文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 解析 YAML Header
            # 匹配 --- ... --- 之间的内容
            header_match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if not header_match:
                return None

            header_yaml = header_match.group(1)
            metadata = yaml.safe_load(header_yaml)
            
            # 正文内容
            instructions = content[header_match.end():].strip()

            return Skill(
                skill_id=skill_id,
                name=metadata.get("name", skill_id),
                description=metadata.get("description", ""),
                instructions=instructions,
                tool_names=metadata.get("tools", []),
                metadata=metadata
            )
        except Exception as e:
            print(f"Error loading skill at {file_path}: {e}")
            return None

    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """获取指定技能"""
        return self._skills.get(skill_id)

    def list_skills(self) -> List[Skill]:
        """列出所有已加载技能"""
        return list(self._skills.values())

# 实例化全局技能管理器 (路径将在 runtime 初始化时确定或注入)
# 目前 discovery_service 已经在使用了，我们未来可以考虑将其整合
