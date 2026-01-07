"""
工厂辅助工具集 (Factory Utilities)

提供 Agent 运行时装配所需的标准化组件集合。
通过预定义中间件栈，确保所有执行单元具备统一的审计、复水与监控能力。
"""

from typing import List
from core.middleware.base import BaseMiddleware
from core.middleware.logging import LoggingMiddleware
from core.middleware.environment import EnvironmentMiddleware
from core.middleware.context import ContextManagerMiddleware
from core.middleware.hydration import ContextHydrationMiddleware
from core.middleware.progress import UIProgressMiddleware

def get_default_middlewares() -> List[BaseMiddleware]:
    """
    获取标准洋葱中间件栈。
    
    层级顺序 (外层 -> 内层)：
    1. 进度冒泡：确保最先捕获并最后完成反馈。
    2. 日志审计：记录全量 I/O。
    3. 环境注入：注入时间等元数据。
    4. 上下文复水：在推理前将 ID 还原为背景文本。
    5. 上下文管理：执行滑动窗口剪枝。
    """
    return [
        UIProgressMiddleware(),
        LoggingMiddleware(),
        EnvironmentMiddleware(),
        ContextHydrationMiddleware(),
        ContextManagerMiddleware(max_history_len=15)
    ]
