import json
import sys
from datetime import datetime
from typing import List, Dict
from core.middleware.base import AgentMiddleware
from core.schema.models import ActionCall, ActionResult

class LoggingMiddleware(AgentMiddleware):
    """
    基础日志中间件 (Standard Output Logger).
    负责将 Agent 的思考、行动与观测实时打印到控制台，
    保持输出的结构化和可读性，不包含任何业务判断逻辑。
    """
    
    def _print_header(self, title: str, color: str = "\033[94m"):
        """打印带颜色的标题栏"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        reset = "\033[0m"
        print(f"{color}{'='*10} {title} [{timestamp}] {'='*10}{reset}")

    async def on_startup(self, agent_id: str, prompt: str):
        self._print_header(f"AGENT STARTUP: {agent_id}", "\033[92m") # Green

    async def on_before_think(self, agent_id: str, history: List[Dict]):
        self._print_header(f"THINKING START: {agent_id}", "\033[96m") # Cyan
        # 打印当前轮次用户的输入（最后一条 user message）
        if history and history[-1]["role"] == "user":
            content = history[-1]["content"]
            # 截断过长的输入
            preview = content[:200] + "..." if len(content) > 200 else content
            print(f"📥 Input: {preview}")
        print("🤔 Stream: ", end="", flush=True)

    async def on_after_think(self, agent_id: str, response: str) -> str:
        # 流式输出结束后换行
        print("\n")
        return response

    async def on_before_action(self, agent_id: str, action: ActionCall):
        self._print_header(f"TOOL CALL: {action.tool_name}", "\033[93m") # Yellow
        print(f"🛠️ Params: {json.dumps(action.params, ensure_ascii=False)}")

    async def on_after_action(self, agent_id: str, action: ActionCall, result: ActionResult):
        color = "\033[92m" if result.status == "success" else "\033[91m" # Green or Red
        self._print_header(f"TOOL RESULT: {action.tool_name}", color)
        
        output_str = str(result.output)
        if len(output_str) > 500:
             output_str = output_str[:500] + f" ... [truncated, total {len(output_str)} chars]"
        
        if result.status == "success":
            print(f"📤 Output: {output_str}")
        else:
            print(f"❌ Error: {result.error}")

    async def on_shutdown(self, agent_id: str):
        self._print_header(f"AGENT SHUTDOWN: {agent_id}", "\033[92m")