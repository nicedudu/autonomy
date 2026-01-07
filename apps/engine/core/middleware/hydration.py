"""
上下文复水中间件 (Context Hydration Middleware)

负责在模型推理前执行引用数据的按需加载。
通过解析执行蓝图中的产物引用标识符，从内存网关检索原始数据并注入当前推理上下文，实现“引用传递”闭环。
"""

from typing import Any, Callable
from core.middleware.base import BaseMiddleware
from core.agent.state import AgentState
from core.agent.memory import memory_gateway

class ContextHydrationMiddleware(BaseMiddleware):
    """
    上下文复水拦截器。
    
    自动完成从 Artifact ID 向背景文本的转化，确保执行单元具备必要的任务上下文。
    """

    async def __call__(self, state: AgentState, next_call: Callable) -> Any:
        # 1. 检索当前激活的任务蓝图
        blueprint = state.metadata.get("active_blueprint")
        
        # 2. 执行复水逻辑
        if blueprint and blueprint.resource.artifact_refs:
            # 调用内存网关执行跨会话检索
            hydrated_content = memory_gateway.hydrate(
                session_id=state.session_id,
                artifact_refs=blueprint.resource.artifact_refs
            )
            
            # 注入上下文变量，供 PromptCompiler 消费
            state.context["hydrated_knowledge"] = hydrated_content
            
        # 3. 继续执行推理链
        return await next_call(state)
