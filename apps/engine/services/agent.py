from typing import Dict, Any, Optional, AsyncGenerator
from services.base import BaseService
from core.session.manager import session_manager
from core.agent.agent import Agent
from core.agent.registry import agent_registry
from core.agent.executor import AgentExecutor

class AgentService(BaseService):
    """
    智能体业务服务。
    """

    def get_agent_config(self, agent_id: str) -> Optional[Dict[str, Any]]:
        # ... (保持原有代码)
        response = self.supabase.table("agents").select(
            "*, llm_providers(*)"
        ).eq("identifier", agent_id).execute()
        return response.data[0] if response.data else None

    async def execute_task(self, agent_id: str, content: str, session_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        驱动智能体执行特定任务。
        """
        # 1. 初始化/恢复会话
        session = session_manager.get_session(session_id)
        if not session:
            session = session_manager.create_session(session_id=session_id)
        
        # 2. 获取智能体 Profile
        profile = agent_registry.get_profile(agent_id)
        if not profile:
            yield {"type": "error", "content": f"未找到智能体规格: {agent_id}"}
            return

        # 3. 实例化 Agent
        agent = Agent.create(profile, session)
        
        # 4. 驱动执行循环
        executor = AgentExecutor()
        async for event in executor.run(agent, input_text=content):
            yield event