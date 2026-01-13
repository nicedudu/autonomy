from core.orchestrator.dispatcher import dispatcher
from services.agent import AgentService

def get_dispatcher():
    """获取全局调度引擎实例。"""
    return dispatcher

def get_agent_service():
    """获取智能体业务服务实例。"""
    return AgentService()

# 导出单例供简单路由使用
agent_service = AgentService()
