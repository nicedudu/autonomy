from typing import Dict, List, Optional, Literal, Any
from core.schema.models import Status

# 内存级存储，模拟数据库持久化
_PLANS_STORE: Dict[str, Dict[str, Any]] = {}
_ACTIVE_PLAN_ID: Optional[str] = None

class PlanningTool:
    """
    任务规划与进度管理工具 (Ported from OpenManus)。
    允许智能体创建、更新和跟踪复杂的任务计划。
    """
    
    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        global _ACTIVE_PLAN_ID
        
        command = params.get("command")
        plan_id = params.get("plan_id") or _ACTIVE_PLAN_ID
        
        if not command:
            return {"status": "error", "message": "必须指定 command 参数 (create/update/mark_step/get)"}

        try:
            if command == "create":
                return self._create(params)
            elif command == "update":
                return self._update(params)
            elif command == "mark_step":
                return self._mark_step(params, plan_id)
            elif command == "get":
                return self._get(plan_id)
            else:
                return {"status": "error", "message": f"未知命令: {command}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        global _ACTIVE_PLAN_ID
        
        title = params.get("title", "未命名计划")
        steps = params.get("steps", [])
        
        if not steps:
            return {"status": "error", "message": "创建计划必须包含 steps 列表"}
            
        import uuid
        plan_id = str(uuid.uuid4())[:8]
        
        plan = {
            "plan_id": plan_id,
            "title": title,
            "steps": steps,
            "step_statuses": ["not_started"] * len(steps),
            "created_at": str(params.get("created_at", ""))
        }
        
        _PLANS_STORE[plan_id] = plan
        _ACTIVE_PLAN_ID = plan_id
        
        return {
            "status": "success", 
            "output": f"计划已创建 (ID: {plan_id})。\n\n{self._format_plan(plan)}"
        }

    def _mark_step(self, params: Dict[str, Any], plan_id: str) -> Dict[str, Any]:
        if not plan_id or plan_id not in _PLANS_STORE:
            return {"status": "error", "message": "未找到活动计划，请先创建。"}
            
        step_index = params.get("step_index")
        status = params.get("status")
        
        if step_index is None or status is None:
            return {"status": "error", "message": "mark_step 需要 step_index 和 status 参数"}
            
        plan = _PLANS_STORE[plan_id]
        if 0 <= step_index < len(plan["steps"]):
            plan["step_statuses"][step_index] = status
            return {
                "status": "success", 
                "output": f"步骤 {step_index} 更新为 {status}。\n\n{self._format_plan(plan)}"
            }
        else:
            return {"status": "error", "message": f"索引 {step_index} 超出范围"}

    def _get(self, plan_id: str) -> Dict[str, Any]:
        if not plan_id or plan_id not in _PLANS_STORE:
             return {"status": "error", "message": "无活动计划。"}
        return {"status": "success", "output": self._format_plan(_PLANS_STORE[plan_id])}

        def sync_from_markdown(self, plan_text: str, plan_id: str = None) -> None:

            """

            [Middleware Hook] 从 Markdown 文本解析并同步计划状态。

            """

            global _ACTIVE_PLAN_ID

            target_id = plan_id or _ACTIVE_PLAN_ID

            

            # 如果没有活动计划，自动创建一个

            if not target_id:

                import uuid

                target_id = str(uuid.uuid4())[:8]

                _ACTIVE_PLAN_ID = target_id

                _PLANS_STORE[target_id] = {

                    "plan_id": target_id,

                    "title": "Auto-Generated Plan",

                    "steps": [],

                    "step_statuses": [],

                    "created_at": ""

                }

    

            if target_id not in _PLANS_STORE:

                return

    

            import re

            # 解析行： - [status] content，增加对 ! 的支持

            pattern = re.compile(r'^\s*-\s*\[([ xX/!])\]\s*(.*)

# 适配 Autonomy 的 run 接口
def run(params: Dict[str, Any]) -> Dict[str, Any]:
    tool = PlanningTool()
    return tool.run(params)
, re.MULTILINE)

            matches = pattern.findall(plan_text)

            

            if not matches:

                return

    

            new_steps = []

            new_statuses = []

            

            status_map = {

                'x': 'completed',

                'X': 'completed',

                '/': 'in_progress',

                ' ': 'not_started',

                '!': 'blocked'

            }

    

            for mark, content in matches:

                new_steps.append(content.strip())

                new_statuses.append(status_map.get(mark, 'not_started'))

    

            # 更新存储

            if new_steps:

                _PLANS_STORE[target_id]["steps"] = new_steps

                _PLANS_STORE[target_id]["step_statuses"] = new_statuses

    

        def _format_plan(self, plan: Dict[str, Any]) -> str:

            from prompts.planning import PLAN_STATUS_ICONS

            

            output = f"Plan: {plan['title']} (ID: {plan['plan_id']})\n"

            output += "=" * 30 + "\n"

            

            for i, (step, status) in enumerate(zip(plan["steps"], plan["step_statuses"])):

                icon = PLAN_STATUS_ICONS.get(status, "[?]")

                output += f"{i}. {icon} {step}\n"

                

            return output

# 适配 Autonomy 的 run 接口
def run(params: Dict[str, Any]) -> Dict[str, Any]:
    tool = PlanningTool()
    return tool.run(params)
