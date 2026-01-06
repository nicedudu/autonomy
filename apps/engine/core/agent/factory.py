from typing import List, Optional

from core.agent.base import BaseAgent
from core.agent.llm_agent import LLMAgent
from core.agent.runtime import AgentRuntime
from core.llm.resolver import LLMConfigResolver
from core.middleware.base import BaseMiddleware
from core.registry.manager import discovery_service


class AgentFactory:
    """
    智能体组装工厂。
    负责根据身份定义，装配出包含配置、中间件和运行时的完整实例。
    """

    @staticmethod
    def create_agent(agent_id: str) -> BaseAgent:
        """
        根据 agent_id 创建 Agent 实例。
        核心配置 (LLM) 强制从数据库实时解析。
        """
        manifest = discovery_service.agents.get(agent_id)
        if not manifest:
            raise ValueError(f"Agent '{agent_id}' 未在代码中定义。")

        # 使用解析器从数据库获取最终配置
        resolver = LLMConfigResolver()
        llm_config = resolver.resolve(agent_id)

        return LLMAgent(manifest, llm_config=llm_config)

    @staticmethod
    def create_runtime(
        agent_id: str,
        middlewares: Optional[List[BaseMiddleware]] = None
    ) -> AgentRuntime:
        """
        创建带标准中间件链的运行时环境。
        """
        agent = AgentFactory.create_agent(agent_id)

        # 加载内置标准中间件 (洋葱模型)
        from core.middleware.context import ContextManagerMiddleware
        from core.middleware.environment import EnvironmentMiddleware

        # 顺序：环境注入 -> 上下文管理 -> 外部自定义中间件
        standard_middlewares = [
            EnvironmentMiddleware(),
            ContextManagerMiddleware(max_history_len=12)
        ]

        if middlewares:
            standard_middlewares.extend(middlewares)

        return AgentRuntime(agent, middlewares=standard_middlewares)
