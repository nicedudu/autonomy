"""
系统日志审计工具 (System Logger)

提供具备生产级复现能力的追踪体系。
Trace 日志包含完整的推理快照：系统指令、对话历史、物理模型标识及原始响应流。
"""

import os
import json
import traceback
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
from typing import Optional, Any, List, Dict

class RuntimeLogger:
    """运行时日志器，执行全量推理链路审计。"""

    def __init__(self):
        self.log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(self.log_dir, exist_ok=True)

        self.logger = logging.getLogger("AutonomyEngine")
        self.logger.setLevel(logging.DEBUG)
        
        if not self.logger.handlers:
            # 1. 运行日志 (runtime.log) - 记录状态变更与异常
            file_path = os.path.join(self.log_dir, "runtime.log")
            handler = TimedRotatingFileHandler(file_path, when="midnight", interval=1, backupCount=30, encoding="utf-8")
            handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-7s | %(message)s'))
            self.logger.addHandler(handler)

            # 2. 全量追踪文件路径 (trace.log)
            self.trace_path = os.path.join(self.log_dir, "trace.log")

    COLORS = {
        "DEBUG": "\033[90m", "INFO": "\033[94m", "SUCCESS": "\033[92m",
        "WARNING": "\033[93m", "ERROR": "\033[91m", "RESET": "\033[0m"
    }

    def _log(self, level: str, msg: str, agent_id: Optional[str] = None):
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        color = self.COLORS.get(level, "")
        prefix = f"[{agent_id}] " if agent_id else ""
        print(f"{color}{ts} | {level:7} | {prefix}{msg}{self.COLORS['RESET']}")
        
        log_msg = f"{prefix}{msg}"
        if level == "ERROR": self.logger.error(log_msg)
        elif level == "WARNING": self.logger.warning(log_msg)
        else: self.logger.info(f"{level} | {log_msg}")

    def trace(self, agent_id: str, model: str, system: str, messages: List[Dict[str, Any]], response: str):
        """记录推理全景快照。"""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        divider = "=" * 100
        section = "-" * 40
        
        # 格式化对话历史
        history_str = ""
        for m in messages:
            history_str += f"[{m.get('role', 'unknown').upper()}] {m.get('content', '')}\n"

        trace_entry = (
            f"\n{divider}\n"
            f"ID: {datetime.now().timestamp()}\n"
            f"TIMESTAMP: {ts} | AGENT: {agent_id} | MODEL: {model}\n"
            f"{section} SYSTEM PROMPT (Rules) {section}\n"
            f"{system}\n\n"
            f"{section} CONVERSATION HISTORY (Context) {section}\n"
            f"{history_str}\n"
            f"{section} RAW MODEL OUTPUT (Content) {section}\n"
            f"{response}\n"
            f"{divider}\n"
        )
        try:
            with open(self.trace_path, "a", encoding="utf-8") as f:
                f.write(trace_entry)
        except Exception as e:
            self._log("ERROR", f"Trace 写入失败: {str(e)}")

    def debug(self, msg: str, agent_id: str = None): self._log("DEBUG", msg, agent_id)
    def info(self, msg: str, agent_id: str = None): self._log("INFO", msg, agent_id)
    def success(self, msg: str, agent_id: str = None): self._log("SUCCESS", msg, agent_id)
    def warning(self, msg: str, agent_id: str = None): self._log("WARNING", msg, agent_id)
    def error(self, msg: str, agent_id: str = None, include_traceback: bool = True):
        self._log("ERROR", msg, agent_id)
        if include_traceback:
            tb = traceback.format_exc()
            if "NoneType: None" not in tb:
                print(f"{self.COLORS['ERROR']}{tb}{self.COLORS['RESET']}")
                self.logger.error(tb)

# 全局单例
logger = RuntimeLogger()