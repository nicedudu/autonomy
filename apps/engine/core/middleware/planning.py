import re
from typing import List, Dict, Optional
from core.middleware.base import AgentMiddleware
from core.schema.models import ActionCall, ActionResult, Status

class PlanningMiddleware(AgentMiddleware):
    """
    高级规划同步中间件 (Active State Synchronization).
    
    1. 意图解析：解析 Agent 输出的 <plan> 标签并同步到持久化存储。
    2. 自动标记：当检测到工具执行成功后，自动将当前步骤标记为已完成。
    3. 状态注入：确保 System Prompt 能感知到最真实的执行进度。
    """
    
    def __init__(self):
        self.plan_pattern = re.compile(r"<plan>(.*?)</plan>", re.DOTALL)
        self.last_action: Optional[ActionCall] = None

    async def on_after_think(self, agent_id: str, response: str) -> str:
        # 1. 自动同步 Markdown 计划
        match = self.plan_pattern.search(response)
        if match:
            plan_content = match.group(1).strip()
            if plan_content:
                try:
                    from tools.planning import PlanningTool
                    tool = PlanningTool()
                    tool.sync_from_markdown(plan_content)
                except Exception:
                    pass
        return response

    async def on_before_action(self, agent_id: str, action: ActionCall):
        # 记录当前执行的 Action，以便在结束后自动推断步骤
        self.last_action = action

    async def on_after_action(self, agent_id: str, action: ActionCall, result: ActionResult):
        # 2. 自动状态跃迁逻辑
        # 如果一个工具（非 planning 工具本身）执行成功，
        # 我们寻找 PlanningTool 中第一个状态为 'not_started' 或 'in_progress' 的步骤并标记完成
        if result.status == Status.SUCCESS and action.tool_name != "planning":
            try:
                from tools.planning import _ACTIVE_PLAN_ID, _PLANS_STORE
                if _ACTIVE_PLAN_ID and _ACTIVE_PLAN_ID in _PLANS_STORE:
                    plan = _PLANS_STORE[_ACTIVE_PLAN_ID]
                    # 找到第一个还没完成的步骤
                    for i, status in enumerate(plan["step_statuses"]):
                        if status != "completed":
                            plan["step_statuses"][i] = "completed"
                            # print(f"[PlanningMiddleware] 🤖 自动将步骤 {i} 标记为已完成")
                            break
            except Exception:
                pass
        
        self.last_action = None
