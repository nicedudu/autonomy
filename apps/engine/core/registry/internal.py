"""
内置智能体名录 (Internal Agent Registry)

本模块定义了系统的静态专家节点。
所有智能体实例的逻辑属性（如角色、能力、推理参数）均在此注册，具体指令逻辑由关联的 Jinja2 模板驱动。
"""

from typing import Dict, List, Optional
from pydantic import BaseModel

class AgentDefinition(BaseModel):
    """智能体静态规格定义。"""
    agent_id: str
    name: str
    role: str
    capabilities: List[str]
    temperature: float = 0.4
    max_tokens: int = 4096
    template_name: str  # 关联的 Jinja2 模板文件标识

INTERNAL_AGENTS: Dict[str, AgentDefinition] = {
    "primary_agent": AgentDefinition(
        agent_id="primary_agent",
        name="首席编排主脑",
        role="Chief Orchestrator",
        capabilities=["web_search", "web_fetch"],
        temperature=0.4,
        template_name="assistant"
    ),
    "researcher": AgentDefinition(
        agent_id="researcher",
        name="深度调研专家",
        role="Analyst",
        capabilities=["web_search", "web_fetch"],
        temperature=0.2,
        template_name="kernel"  # 专家节点通用逻辑内核
    )
}

def get_agent_definition(agent_id: str) -> Optional[AgentDefinition]:
    """根据标识符检索智能体定义。"""
    return INTERNAL_AGENTS.get(agent_id)