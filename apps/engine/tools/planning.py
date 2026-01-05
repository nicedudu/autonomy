import json
import uuid
from typing import Any, Dict, List, Optional

from tools.base import tool

# 持久化计划存储（内存级）
_PLANS_STORE: Dict[str, Dict[str, Any]] = {}
_ACTIVE_PLAN_ID: Optional[str] = None


class PlanningManager:
    """
    内部计划管理逻辑封装。
    """

    def execute(self, params: Dict[str, Any], agent_id: str = "primary_agent") -> Dict[str, Any]:
        global _ACTIVE_PLAN_ID
        command = params.get("command")
        plan_id = params.get("plan_id") or _ACTIVE_PLAN_ID

        if command == "create":
            return self._create(params)

        if not plan_id or plan_id not in _PLANS_STORE:
            return {"status": "error", "message": "未找到活动计划"}

        if command == "mark_step":
            return self._mark_step(plan_id, params)
        elif command == "get":
            return {"status": "success", "output": self.format_plan(_PLANS_STORE[plan_id])}

        return {"status": "error", "message": f"不支持的指令: {command}"}

    def _create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        global _ACTIVE_PLAN_ID
        plan_id = str(uuid.uuid4())[:8]
        steps = params.get("steps", [])
        if not steps:
            return {"status": "error", "message": "创建计划至少需要一个步骤"}

        plan = {
            "plan_id": plan_id,
            "title": params.get("title", "Master Plan"),
            "steps": steps,
            "step_statuses": ["not_started"] * len(steps)
        }
        _PLANS_STORE[plan_id] = plan
        _ACTIVE_PLAN_ID = plan_id
        return {"status": "success", "output": f"计划已创建: {plan_id}", "plan": plan}

    def _mark_step(self, plan_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        plan = _PLANS_STORE[plan_id]
        idx = params.get("step_index")
        status = params.get("status", "completed")
        if idx is not None and 0 <= idx < len(plan["steps"]):
            plan["step_statuses"][idx] = status
            return {"status": "success", "output": f"步骤 {idx} 状态已更新为 {status}"}
        return {"status": "error", "message": "索引无效"}

    def sync_from_json(self, plan_json: str, agent_id: str = "primary_agent") -> None:
        """
        从结构化 JSON 同步计划。
        """
        global _ACTIVE_PLAN_ID
        try:
            # 1. 剥离可能存在的 markdown 代码块包裹
            clean_json = plan_json.replace(
                "```json", "").replace("```", "").strip()
            new_data = json.loads(clean_json)
            if not isinstance(new_data, list):
                return
        except Exception:
            return

        if not _ACTIVE_PLAN_ID:
            self._create({"steps": [item.get("step") for item in new_data]})

        plan = _PLANS_STORE[_ACTIVE_PLAN_ID]

        if agent_id == "primary_agent":
            # 主控节点：同步结构与状态
            plan["steps"] = [item.get("step") for item in new_data]
            plan["step_statuses"] = [
                item.get("status", "not_started") for item in new_data]
        else:
            # 执行节点：仅同步状态
            for i, old_step in enumerate(plan["steps"]):
                for new_item in new_data:
                    if old_step.strip() == new_item.get("step", "").strip():
                        plan["step_statuses"][i] = new_item.get(
                            "status", "not_started")
                        break

    def format_plan(self, plan: Dict[str, Any]) -> str:
        lines = [f"Plan: {plan['title']} ({plan['plan_id']})", "="*30]
        for i, (step, status) in enumerate(zip(plan["steps"], plan["step_statuses"])):
            lines.append(f"{i}. [{status}] {step}")
        return "\n".join(lines)


@tool()
async def planning(command: str, title: str = None, steps: List[str] = None, step_index: int = None, status: str = None) -> Dict[str, Any]:
    """
    任务计划管理工具。当任务超过3步时，必须使用此工具记录进度。

    Args:
        command: 指令 (create/mark_step/get)。
        title: 标题。
        steps: 步骤列表。
        step_index: 步骤索引。
        status: 状态标识。
    """
    mgr = PlanningManager()
    return mgr.execute(locals())


async def run(params: Dict[str, Any]) -> Dict[str, Any]:
    return await planning(**params)
