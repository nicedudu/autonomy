from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class Skill(BaseModel):
    """
    智能体技能模型 (Codex Style)。
    表示一个自包含的领域能力包。
    """
    skill_id: str
    name: str
    description: str
    instructions: str                # 对应 SKILL.md 的 Markdown 文本内容
    tool_names: List[str] = Field(default_factory=list) # 该技能关联的工具名称列表
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def compile_instruction(self) -> str:
        """格式化技能指令，用于注入 Prompt"""
        return f"### Skill: {self.name} ({self.skill_id})\n{self.instructions}\n"
