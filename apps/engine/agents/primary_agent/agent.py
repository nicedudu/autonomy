"""
首席编排主脑 (Primary Agent)

作为系统的核心调度节点，负责复杂任务的意图拆解与工作流编排。
"""

from core.agent.profile import AgentProfile

profile = AgentProfile(
    agent_id="primary_agent",
    name="首席编排主脑",
    role_description="你是一个精通任务拆解与资源编排的高级助理。擅长将复杂意图转化为结构化的工作流清单（Blueprint）。",
    template_id="assistant",
    # 授权列表：补全审计所需的全量文件操作权限
    capability_mask=[
        "web_search", 
        "web_fetch", 
        "researcher", 
        "list_workspace_files",
        "read_workspace_file"
    ],
    inference_params={
        "temperature": 0.1,
        "max_tokens": 8192
    }
)
