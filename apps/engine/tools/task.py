"""
任务状态追踪工具 (Task Context Tracker)

管理 Agent 执行复杂任务时的 SOP 进度、多步计划及中间状态。
"""

import uuid
from typing import Any, Dict, List, Optional

from core.tools.base import tool

# 内存级存储 (生产环境建议外置)
_TASK_REGISTRY: Dict[str, Dict[str, Any]] = {}


@tool()
async def manage_task_steps(
    operation: str,
    steps: Optional[List[str]] = None,
    current_step_index: Optional[int] = None,
    status_update: Optional[str] = None
) -> Dict[str, Any]:
    """
    追踪多步骤复杂任务的执行进度。
    当任务涉及 3 个以上逻辑环节时，应使用此工具维持状态一致性。

    Args:
        operation: 操作类型 (create: 创建计划, update: 更新状态, list: 获取当前进度)。
        steps: 仅在 create 时提供，定义所有逻辑步骤。
        current_step_index: 要更新的步骤索引。
        status_update: 步骤的新状态 (如: "completed", "failed")。
    """
    if operation == "create":
        if not steps:
            return {"status": "error", "message": "创建任务需提供步骤列表"}
        task_id = str(uuid.uuid4())[:8]
        _TASK_REGISTRY[task_id] = {
            "steps": steps,
            "statuses": ["pending"] * len(steps)
        }
        return {"status": "success", "task_id": task_id, "data": _TASK_REGISTRY[task_id]}

    # 简化逻辑：仅展示核心概念
    return {"status": "success", "message": f"操作 {operation} 已接收", "registry_size": len(_TASK_REGISTRY)}
