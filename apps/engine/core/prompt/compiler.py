"""
提示词编译器 (Prompt Compiler)
"""

import time
import json
from pathlib import Path
from typing import Any, Dict, Optional

import jinja2
from core.agent.profile import AgentProfile

class PromptCompiler:
    def __init__(self):
        current_dir = Path(__file__).parent.resolve()
        template_dir = current_dir.parent.parent / "prompts"
        
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=jinja2.StrictUndefined
        )

    def _get_render_context(self, session: Any, profile: Optional[AgentProfile] = None) -> Dict[str, Any]:
        """
        合成渲染上下文。
        实现“定义+状态”双维度融合，为模型提供显性任务看板。
        """
        is_session_obj = hasattr(session, "id") and hasattr(session, "metadata")
        session_id = session.id if is_session_obj else getattr(session, "session_id", "Unknown")
        metadata = session.metadata if is_session_obj else getattr(session, "context", {})
        
        # 提取会话级编排进度
        local_nodes = metadata.get("session_blueprint_nodes", {})
        
        # 【关键增强】：构建具备状态感知的看板数据
        # 不再仅仅 dump 原始定义，而是合并实时执行状态
        formatted_nodes = {}
        for node_id, node_data in local_nodes.items():
            # 基础定义信息
            info = {
                "id": node_id,
                "task": node_data.get("task_name"),
                "capability": node_data.get("capability"),
                "status": node_data.get("status", "PENDING"), # 显性注入状态
                "deps": node_data.get("dependencies", [])
            }
            # 如果任务已完成，注入结果摘要以辅助后续决策
            if info["status"] == "COMPLETED" and "output" in node_data:
                # 截断长结果，保持看板精简
                raw_out = str(node_data["output"])
                info["result_summary"] = (raw_out[:200] + "...") if len(raw_out) > 200 else raw_out
            
            formatted_nodes[node_id] = info

        render_vars = {
            "current_time": metadata.get("current_time", time.strftime("%Y-%m-%d %H:%M:%S")),
            "agent_name": profile.name if profile else "执行单元",
            "agent_id": profile.agent_id if profile else "unknown_agent",
            "agent_role": profile.role_description if profile else "系统助理",
            "session_id": session_id,
            "authorized_tools": metadata.get("authorized_tools", "[]"),
            "few_shot_context": metadata.get("few_shot_context", ""),
            # 注入高度语义化的任务进度看板
            "workflow_progress": json.dumps(formatted_nodes, ensure_ascii=False, indent=2) if formatted_nodes else None
        }
        
        # 补全元数据空间
        for key in ["team_roster", "skill_docs", "hydrated_knowledge", "history_summary"]:
            render_vars[key] = metadata.get(key, "")

        render_vars.update(metadata)
        return render_vars

    def compile_agent_prompt(self, profile: AgentProfile, session: Any) -> str:
        """根据 AgentProfile 与会话状态合成指令。"""
        try:
            render_context = self._get_render_context(session, profile)
            template = self.env.get_template(f"{profile.template_id}.j2")
            return template.render(**render_context)
        except Exception as e:
            raise RuntimeError(f"指令编译异常 ({profile.agent_id}): {str(e)}")

# 全局单例提示词编译器
prompt_compiler = PromptCompiler()
