"""
中间件管理器 (Middleware Manager)
"""

from typing import List, Dict, Type, Any
from core.middleware.base import BaseMiddleware
from core.agent.agent import Agent

class MiddlewareManager:
    """
    中间件注册与组装中心。
    """

    def __init__(self):
        # 存储模型：{标识符: 中间件类}
        self._registry: Dict[str, Type[BaseMiddleware]] = {}
        # 定义系统级强制开启的全局中间件标识符
        self._global_middlewares: List[str] = []

    def register(self, identifier: str, middleware_cls: Type[BaseMiddleware], is_global: bool = False):
        """
        注册中间件。
        """
        self._registry[identifier] = middleware_cls
        if is_global and identifier not in self._global_middlewares:
            self._global_middlewares.append(identifier)

    def assemble(self, agent: Agent) -> List[BaseMiddleware]:
        """
        组装适用于当前智能体的中间件执行链。
        """
        # 合并标识符
        active_identifiers = set(self._global_middlewares + agent.profile.middlewares)
        
        instances = []
        for ident in active_identifiers:
            mw_cls = self._registry.get(ident)
            if mw_cls:
                instances.append(mw_cls())
        
        # 按照优先级排序
        return sorted(instances, key=lambda x: getattr(x, "priority", 100))

# 导出全局单例
middleware_manager = MiddlewareManager()

# --- 自动注册系统核心中间件 ---
from core.middleware.logging import LoggingMiddleware
from core.middleware.context import ContextMiddleware

middleware_manager.register("logging", LoggingMiddleware, is_global=True)
middleware_manager.register("context", ContextMiddleware, is_global=True)