from fastapi import APIRouter, HTTPException
from core.agent.registry import agent_registry

router = APIRouter(prefix="/api/agents", tags=["agent"])

@router.get("")
async def list_available_agents():
    """
    列出当前物理目录中发现的所有可用智能体。
    """
    try:
        agent_ids = agent_registry.get_agents()
        agents = []
        for aid in agent_ids:
            profile = agent_registry.get_profile(aid)
            if profile:
                agents.append({
                    "id": aid,
                    "identifier": aid,
                    "name": profile.name,
                    "role": profile.role_description,
                    "avatar": f"https://api.dicebear.com/7.x/bottts/svg?seed={aid}"
                })
        return agents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{agent_id}/profile")
async def get_agent_details(agent_id: str):
    """
    检索指定智能体的规格详情。
    """
    profile = agent_registry.get_profile(agent_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"智能体 {agent_id} 未找到。")
    return profile