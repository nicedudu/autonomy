from datetime import datetime
from typing import List, Optional
from prompts.system import SYSTEM_PROMPT_TEMPLATE
from prompts.planning import PLANNING_PROTOCOL, PLAN_STATUS_ICONS
from prompts.toolcall import TOOLCALL_PROTOCOL

class PromptCompiler:
    """
    提示词编译器。
    负责将静态指令模板与运行时动态数据（时间、全局事实、计划进度）进行高性能组装。
    """

    @staticmethod
    def compile_system_prompt(
        dynamic_capabilities: str,
        team_roster: str = "",
        global_facts: Optional[List[str]] = None
    ) -> str:
        """
        组装最终的系统级指令（System Prompt）。
        """
        current_time = datetime.now().strftime("%Y-%m-%d %A %H:%M:%S")
        
        # 1. 组装全局事实
        facts_section = ""
        if global_facts:
            facts_text = "\n".join(global_facts[-8:])
            facts_section = f"\n\n[组织共识事实]:\n{facts_text}"

        # 2. 注入实时计划状态 (Live Plan State)
        current_plan_section = ""
        try:
            from tools.planning import _ACTIVE_PLAN_ID, _PLANS_STORE
            if _ACTIVE_PLAN_ID and _ACTIVE_PLAN_ID in _PLANS_STORE:
                plan = _PLANS_STORE[_ACTIVE_PLAN_ID]
                plan_text = f"Plan: {plan['title']} (ID: {plan['plan_id']})\n"
                
                for i, (step, status) in enumerate(zip(plan["steps"], plan["step_statuses"])):
                    icon = PLAN_STATUS_ICONS.get(status, "[?]")
                    plan_text += f"{i}. {icon} {step}\n"
                
                current_plan_section = (
                    f"\n\n[当前活动计划 - LIVE PLAN STATE]\n{plan_text}\n"
                    "注意：这是系统实时记录的计划状态。请依据此表推进任务，并及时更新状态。"
                )
        except (ImportError, Exception):
            pass

        # 3. 模板填充
        return SYSTEM_PROMPT_TEMPLATE.format(
            current_time=current_time,
            planning_protocol=PLANNING_PROTOCOL,
            toolcall_protocol=TOOLCALL_PROTOCOL,
            dynamic_capabilities=dynamic_capabilities,
            team_roster=team_roster,
            facts_section=facts_section,
            current_plan_section=current_plan_section
        )

# 全局编译器单例
prompt_compiler = PromptCompiler()
