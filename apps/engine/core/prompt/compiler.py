import jinja2
from typing import Dict, Any
from core.registry.internal import AgentDefinition
from core.agent.state import AgentState

class PromptCompiler:
    """
    基于 Jinja2 的生产级提示词编译器。
    支持动态变量注入、逻辑判断及复杂的上下文组装。
    """

    def __init__(self):
        self.env = jinja2.Environment(
            # 采用更安全的配置
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True
        )

    def compile_system_prompt(self, definition: AgentDefinition, state: AgentState) -> str:
        """
        使用 Jinja2 渲染最终的 System Prompt。
        """
        template_str = definition.instruction_template
        
        # 1. 组装全局动态变量
        context_vars = {
            "current_time": state.context.get("current_time", "Unknown"),
            "agent_name": definition.name,
            "agent_role": definition.role,
            "session_id": state.session_id,
            "history_len": len(state.history),
            "usage": state.usage,
            "context": state.context,
            "metadata": state.metadata,
            "skill_docs": state.context.get("skill_docs", ""),
            "team_roster": state.context.get("team_roster", ""),
            "artifacts_summary": self._summarize_artifacts(state.artifacts)
        }

        # 2. 编译并渲染模板
        try:
            template = self.env.from_string(template_str)
            return template.render(**context_vars)
        except Exception as e:
            # 编译失败时，退回到原始模板并记录错误
            print(f"\033[91m[PromptCompiler Error] Failed to render template: {e}\033[0m")
            return template_str

    def _summarize_artifacts(self, artifacts: Dict[str, Any]) -> str:
        """为 Prompt 提供生成的产物摘要"""
        if not artifacts:
            return ""
        summary = ["Current active artifacts:"]
        for key, value in artifacts.items():
            summary.append(f"- ID: {key} (Size: {len(str(value))} chars)")
        return "\n".join(summary)

# 单例模式供 Runtime 调用
prompt_compiler = PromptCompiler()