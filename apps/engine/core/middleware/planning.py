import re
import json
from typing import List, Dict, Optional
from core.middleware.base import AgentMiddleware
from core.schema.models import ActionCall, ActionResult, Status

class PlanningMiddleware(AgentMiddleware):
    """
    结构化规划同步中间件。
    负责解析 <plan> 标签内的 JSON 数据并实现跨节点同步。
    """
    
    def __init__(self):
        self.plan_pattern = re.compile(r"<plan>(.*?)</plan>", re.DOTALL)

    async def on_after_think(self, agent_id: str, response: str) -> str:
        # 1. 解析 JSON 计划
        match = self.plan_pattern.search(response)
        if match:
            plan_json = match.group(1).strip()
            if plan_json:
                try:
                    from tools.planning import PlanningManager
                    mgr = PlanningManager()
                    mgr.sync_from_json(plan_json, agent_id=agent_id)
                except Exception:
                    pass
            return response
        
        # 2. 自动补全逻辑（若模型漏掉计划，由中间件从状态库读取并注入最新的 JSON 块）
        try:
            from tools.planning import _ACTIVE_PLAN_ID, _PLANS_STORE
            if _ACTIVE_PLAN_ID and _ACTIVE_PLAN_ID in _PLANS_STORE:
                plan = _PLANS_STORE[_ACTIVE_PLAN_ID]
                plan_list = [
                    {"step": s, "status": st} 
                    for s, st in zip(plan["steps"], plan["step_statuses"])
                ]
                # 使用标准的 markdown 代码块包裹 JSON
                plan_text = f"<plan>\n```json\n{json.dumps(plan_list, ensure_ascii=False, indent=2)}\n```\n</plan>"
                response = plan_text + "\n\n" + response
        except Exception:
            pass

        return response

    async def on_after_action(self, agent_id: str, action: ActionCall, result: ActionResult):
        """工具执行成功后，自动推进状态机。"""
        if result.status == Status.SUCCESS and action.tool_name != "planning":
            try:
                from tools.planning import _ACTIVE_PLAN_ID, _PLANS_STORE
                if _ACTIVE_PLAN_ID and _ACTIVE_PLAN_ID in _PLANS_STORE:
                    plan = _PLANS_STORE[_ACTIVE_PLAN_ID]
                    for i, status in enumerate(plan["step_statuses"]):
                        if status != "completed":
                            plan["step_statuses"][i] = "completed"
                            break
            except Exception:
                pass
