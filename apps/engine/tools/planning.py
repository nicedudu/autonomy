from typing import Dict, List, Optional, Any
from tools.base import BaseTool

_PLANS_STORE: Dict[str, Dict[str, Any]] = {}
_ACTIVE_PLAN_ID: Optional[str] = None

class PlanningTool(BaseTool):
    """
    任务规划与进度管理工具。
    """
    
    @property
    def name(self) -> str:
        return "planning"

    @property
    def description(self) -> str:
        return "用于创建长程任务计划、更新步骤状态及跟踪进度。当任务步骤超过 3 步时必须使用。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "enum": ["create", "update", "mark_step", "get"],
                    "description": "执行的操作"
                },
                "title": {"type": "string", "description": "计划标题"},
                "steps": {"type": "array", "items": {"type": "string"}, "description": "计划步骤列表"},
                "step_index": {"type": "integer", "description": "步骤索引"},
                "status": {
                    "type": "string",
                    "enum": ["not_started", "in_progress", "completed", "blocked"],
                    "description": "步骤新状态"
                }
            },
            "required": ["command"]
        }

    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        global _ACTIVE_PLAN_ID
        command = params.get("command")
        plan_id = params.get("plan_id") or _ACTIVE_PLAN_ID
        
        # 逻辑复用之前的实现（此处精简）
        return {"status": "success", "output": "计划更新成功"}

    def sync_from_markdown(self, plan_text: str, plan_id: str = None) -> None:
        # ... 逻辑复用之前的实现 ...
        pass

async def run(params: Dict[str, Any]) -> Dict[str, Any]:
    return await PlanningTool().run(params)