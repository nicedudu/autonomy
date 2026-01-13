"""
智能体中间件标准规范 (Agent Middleware Specification)

本模块定义了执行引擎的拦截器协议。
采用基于 Session 注入的生命周期钩子（Hooks）模式，实现对“感知-决策-执行”全链路的精确控制。
支持横切关注点（如 Token 审计、上下文裁剪、权限拦截）的模块化解耦。
"""

from typing import Any, Dict, List, Optional
from core.session.session import Session
from core.agent.profile import AgentProfile
from core.llm.schema import LLMResponse, LLMMessage
from core.protocol.schema import ProtocolResponse

class BaseMiddleware:
    """
    中间件抽象基类。
    """
    priority: int = 100 # 执行优先级，越小越靠前

    async def on_agent_start(self, session: Session, profile: AgentProfile):
        """
        [生命周期] 智能体启动钩子。
        
        触发时机：AgentExecutor.run 启动瞬间。
        典型用途：初始化 Session 元数据、加载长期记忆。
        """
        pass

    async def pre_inference(self, session: Session, messages: List[LLMMessage]):
        """
        [模型边界] 推理前置钩子。
        
        触发时机：LLM 推理请求发起前。
        典型用途：滑动窗口裁剪、提示词动态注入。
        """
        pass

    async def post_inference(self, session: Session, response: LLMResponse):
        """
        [模型边界] 推理后置钩子。
        
        触发时机：收到 LLM 原始回复后。
        典型用途：Token 消耗审计、推理结果预清洗。
        """
        pass

    async def pre_dispatch(self, session: Session, proto: ProtocolResponse):
        """
        [执行边界] 派发前置钩子。
        
        触发时机：编排意图解析后，WorkflowPipeline 启动前。
        典型用途：安全护栏校验、执行权限拦截、参数脱敏。
        """
        pass

    async def post_dispatch(self, session: Session, snapshot: Any):
        """
        [执行边界] 派发后置钩子。
        
        触发时机：WorkflowPipeline 执行完毕后。
        典型用途：执行产物归档、长效产物持久化。
        """
        pass

    async def on_agent_end(self, session: Session):
        """
        [生命周期] 智能体结束钩子。
        
        触发时机：ReAct 循环终止或达成结论后。
        典型用途：清理临时资源、发送审计总结。
        """
        pass
