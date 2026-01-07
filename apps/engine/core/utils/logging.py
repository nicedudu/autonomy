"""
系统日志审计工具 (System Logger)

提供具备生产级观测能力的彩色格式化日志输出。
支持全量堆栈追踪、耗时统计及执行单元标识，确保分布式环境下的透明化调试。
"""

import time
import traceback
from datetime import datetime
from typing import Optional

class RuntimeLogger:
    """运行时日志器。"""

    COLORS = {
        "DEBUG": "\033[90m", # 灰色
        "INFO": "\033[94m",  # 蓝色
        "SUCCESS": "\033[92m", # 绿色
        "WARNING": "\033[93m", # 黄色
        "ERROR": "\033[91m",   # 红色
        "RESET": "\033[0m"
    }

    @staticmethod
    def _log(level: str, msg: str, agent_id: Optional[str] = None):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        color = RuntimeLogger.COLORS.get(level, "")
        reset = RuntimeLogger.COLORS["RESET"]
        prefix = f"[{agent_id}] " if agent_id else ""
        print(f"{color}{timestamp} | {level:7} | {prefix}{msg}{reset}")

    @staticmethod
    def debug(msg: str, agent_id: Optional[str] = None):
        RuntimeLogger._log("DEBUG", msg, agent_id)

    @staticmethod
    def info(msg: str, agent_id: Optional[str] = None):
        RuntimeLogger._log("INFO", msg, agent_id)

    @staticmethod
    def success(msg: str, agent_id: Optional[str] = None):
        RuntimeLogger._log("SUCCESS", msg, agent_id)

    @staticmethod
    def warning(msg: str, agent_id: Optional[str] = None):
        RuntimeLogger._log("WARNING", msg, agent_id)

    @staticmethod
    def error(msg: str, agent_id: Optional[str] = None, include_traceback: bool = True):
        RuntimeLogger._log("ERROR", msg, agent_id)
        if include_traceback:
            # 仅在有错误上下文时打印堆栈
            if "NoneType: None" not in traceback.format_exc():
                print(f"{RuntimeLogger.COLORS['ERROR']}{traceback.format_exc()}{RuntimeLogger.COLORS['RESET']}")

# 全局单例
logger = RuntimeLogger()