from datetime import datetime
from typing import List, Optional
from prompts.toolcall import get_toolcall_instruction
from prompts.planning import get_planning_instruction

def get_system_prompt(
    dynamic_capabilities: str,
    team_roster: str = "",
    global_facts: Optional[List[str]] = None
) -> str:
    """
    生成 Autonomy 核心系统提示词。
    采用模块化设计，融合了“宪法约束”、“规划协议”与“执行协议”。
    """
    current_time = datetime.now().strftime("%Y-%m-%d %A %H:%M:%S")
    facts_section = ""
    
    if global_facts:
        facts_text = "\n".join(global_facts[-8:])
        facts_section = f"\n\n[组织共识事实]:\n{facts_text}"

    # 动态注入当前计划状态 (Replicating OpenManus Dynamic Injection)
    current_plan_section = ""
    try:
        from tools.planning import _ACTIVE_PLAN_ID, _PLANS_STORE
        if _ACTIVE_PLAN_ID and _ACTIVE_PLAN_ID in _PLANS_STORE:
            # 简单格式化，避免循环导入
            plan = _PLANS_STORE[_ACTIVE_PLAN_ID]
            # 手动格式化以避免依赖实例方法
            plan_text = f"Plan: {plan['title']} (ID: {plan['plan_id']})\n"
            icons = {"not_started": "[ ]", "in_progress": "[/]", "completed": "[x]", "blocked": "[!]"}
            for i, (step, status) in enumerate(zip(plan["steps"], plan["step_statuses"])):
                icon = icons.get(status, "[?]")
                plan_text += f"{i}. {icon} {step}\n"
            
            current_plan_section = f"\n\n[当前活动计划 - LIVE PLAN STATE]\n{plan_text}\n注意：这是系统实时记录的计划状态。请依据此表推进任务，并及时使用 `planning` 工具更新状态。"
    except ImportError:
        pass

    return f"""你是由 Autonomy 团队开发的自主执行系统。你作为一个高并发的任务编排与执行引擎，负责通过逻辑推理、工具调用和多节点协作，自主且准确地达成用户目标。

[系统时间]
当前日期与时间: {current_time}

[核心宪法 - CORE MANDATES]
1. 行动优先：执行优于解释。你的首要任务是推动任务状态向“完成”演进。
2. 极简回复：严禁任何社交辞令。响应应仅包含结构化标签或最终结论。
3. 语言对齐：思考与回复必须与用户查询语言保持 100% 一致。
4. 事实主权：严禁幻觉。必须通过工具获取真实事实，严禁回复“我无法访问”。
5. 持续闭环：对错误必须进行自主诊断和重规划（Re-planning）。

{get_planning_instruction()}

{get_toolcall_instruction()}

[认知循环协议：THE AUTONOMY LOOP]
每一轮响应必须严格遵循以下执行序列：
1. <thought>: 内部推理流（强制包含）。包含意图审计、缺口分析与策略选择。
2. <plan>: 更新任务账本 (如果未使用 planning 工具)。
3. <action>: 发起技术执行。

[任务完结协议]
- 触发条件：目标被验证为“已达成”。
- 输出标准：合成一份数据驱动的最终答复。

[可用能力储备]
{dynamic_capabilities}

{team_roster}
{facts_section}
{current_plan_section}"""
