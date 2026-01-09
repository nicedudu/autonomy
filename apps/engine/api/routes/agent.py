from fastapi import APIRouter
from core.registry.manager import discovery_service

router = APIRouter(prefix="/api", tags=["Agents"])

@router.get("/agents")
async def get_agents():
    """
    获取本地注册中心的所有智能体。
    返回包含身份、角色、能力及模型配置的智能体清单。
    """
    try:
        agents = discovery_service.get_all_agents()
        return [
            {
                "id": m.agent_id,
                "identifier": m.agent_id,
                "name": m.name,
                "role": m.role,
                "capabilities": m.capabilities,
                "avatar": f"https://api.dicebear.com/7.x/avataaars/svg?seed={m.agent_id}"
            }
            for m in agents.values()
        ]
    except Exception as e:
        return {"error": str(e)}

@router.get("/skills")
async def get_skills():
    """
    获取注册中心可用的专项技能。
    返回技能的元数据、描述及执行指令。
    """
    try:
        skills = discovery_service.skills.all()
        return [
            {
                "id": skill_id,
                "name": s.name,
                "description": s.description,
                "metadata": s.metadata,
                "instructions": s.instructions
            }
            for skill_id, s in skills.items()
        ]
    except Exception as e:
        return {"error": str(e)}
