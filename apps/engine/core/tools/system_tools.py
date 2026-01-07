"""
系统级原子工具 (System Tools)

提供由引擎内核直接驱动的基础能力，包括产物检索、委派反馈等。
这些工具绕过物理文件系统，直接操作内存网关与总线。
"""

from typing import Any, Dict
from core.agent.memory import memory_gateway
from core.tools.base import BaseTool

async def read_artifact_func(session_id: str, artifact_id: str) -> Dict[str, Any]:
    """从内存网关中检索指定产物的内容。"""
    artifact = memory_gateway.retrieve(session_id, artifact_id)
    if not artifact:
        return {"status": "error", "message": f"未找到产物: {artifact_id}"}
    
    return {
        "status": "success",
        "id": artifact.id,
        "type": artifact.type,
        "content": artifact.content
    }

# 实例化系统工具
read_artifact_tool = BaseTool(
    name="read_artifact",
    description="从共享内存中检索指派任务的背景数据或前序任务结果。",
    parameters={
        "type": "object",
        "properties": {
            "artifact_id": {"type": "string", "description": "产物唯一引用 ID"}
        },
        "required": ["artifact_id"]
    },
    func=read_artifact_func
)