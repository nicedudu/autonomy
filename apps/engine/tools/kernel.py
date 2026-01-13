"""
内核控制工具 (Kernel Operations)
"""

from typing import Any, Dict
from core.agent.memory import memory_gateway
from core.tools.base import tool
from core.session.session import Session

@tool()
async def get_artifact_content(artifact_id: str, session: Session) -> Dict[str, Any]:
    """
    从当前会话的隔离内存中检索特定的产物内容。
    """
    # 严格遵循 Session 隔离
    artifact = memory_gateway.retrieve(session.id, artifact_id)
    if not artifact:
        return {"status": "error", "message": f"在当前会话中未找到授权产物: {artifact_id}"}
    
    return {
        "status": "success",
        "artifact": {
            "id": artifact.id,
            "type": artifact.type,
            "content": artifact.content
        }
    }
