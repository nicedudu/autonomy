"""
提示词编译器 (Prompt Compiler)

负责将结构化模型、运行时上下文与 Jinja2 模板库进行流水线合成。
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import jinja2
from core.agent.state import AgentState
from core.registry.internal import AgentDefinition
from core.schema.collaboration import ExecutionBlueprint

class PromptCompiler:
    """
    生产级提示词编译器。
    
    实现逻辑宪法 (Kernel) 与业务蓝图 (Blueprint) 的自动化装配。
    """

    def __init__(self):
        current_dir = Path(__file__).parent.resolve()
        template_dir = current_dir.parent.parent / "prompts" / "templates"
        
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=jinja2.StrictUndefined
        )

    def _get_render_context(self, state: AgentState, definition: Optional[AgentDefinition] = None) -> Dict[str, Any]:
        """合成全量渲染上下文，显式补全模板变量以通过严格模式校验。"""
        # 1. 确立模板变量基准集
        render_vars = {
            "current_time": state.context.get("current_time", "Unknown"),
            "agent_name": definition.name if definition else "执行节点",
            "agent_role": definition.role if definition else "Atomic Task Executor",
            "session_id": state.session_id,
            "skill_docs": state.context.get("skill_docs", ""),
            "team_roster": state.context.get("team_roster", ""),
            # 显式初始化可能缺失的动态注入变量
            "authorized_tools": state.context.get("authorized_tools"),
            "hydrated_knowledge": state.context.get("hydrated_knowledge")
        }
        
        # 2. 合并 state.context 中的其余动态数据
        render_vars.update(state.context)
        
        return render_vars

    def compile_blueprint(self, blueprint: ExecutionBlueprint, state: AgentState) -> str:
        """根据任务蓝图与实时状态合成全量指令。"""
        try:
            render_context = self._get_render_context(state)
            
            kernel_tmpl = self.env.get_template("kernel.j2")
            kernel_content = kernel_tmpl.render(**render_context)

            blueprint_tmpl = self.env.get_template("blueprint.j2")
            spec_content = blueprint_tmpl.render(**blueprint.model_dump())

            return f"{kernel_content}\n\n{spec_content}"
        except Exception as e:
            raise RuntimeError(f"蓝图指令编译异常: {str(e)}")

    def compile_agent_prompt(self, definition: AgentDefinition, state: AgentState) -> str:
        """根据静态定义与实时状态合成指令。"""
        try:
            render_context = self._get_render_context(state, definition)
            template = self.env.get_template(f"{definition.template_name}.j2")
            return template.render(**render_context)
        except Exception as e:
            raise RuntimeError(f"智能体指令编译异常 ({definition.agent_id}): {str(e)}")

# 全局单例提示词编译器
prompt_compiler = PromptCompiler()
