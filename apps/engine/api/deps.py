from core.orchestrator import Orchestrator

# 全局任务编排器单例
# 所有的路由模块应通过此变量访问编排功能，确保状态同步
orchestrator = Orchestrator()
