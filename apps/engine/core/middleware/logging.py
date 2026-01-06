import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from core.middleware.base import AgentMiddleware
from core.agent.state import AgentState, AgentMessage, MessageRole

class LoggingMiddleware(AgentMiddleware):
    """
    基础日志中间件 (Standard Output Logger).
    负责将 Agent 的思考、行动与观测实时打印到控制台。
    """
    
    def _print_header(self, title: str, color: str = "\033[94m"):
        """打印带颜色的标题栏"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        reset = "\033[0m"
        print(f"{color}{'='*10} {title} [{timestamp}] {'='*10}{reset}")

    async def on_before_step(self, state: AgentState) -> Optional[Dict[str, Any]]:
        self._print_header(f"STEP {state.step_count} START: {state.agent_id}", "\033[96m")
        
        # 打印最后一条用户或工具消息作为输入参考
        if state.history:
            last_msg = state.history[-1]
            preview = last_msg.content[:200] + "..." if len(last_msg.content) > 200 else last_msg.content
            print(f"📥 Last Msg ({last_msg.role}): {preview}")
        
        # [DEBUG] 打印编译后的系统提示词 (由 Runtime 在 state.metadata 中注入)
        if "compiled_system_prompt" in state.metadata:
            self._print_header("COMPILED SYSTEM PROMPT", "\033[90m") # Gray
            print(state.metadata["compiled_system_prompt"])
            self._print_header("END PROMPT", "\033[90m")

        print("🤔 Thinking...")
        return None

    async def on_after_thought(self, state: AgentState, thought_msg: AgentMessage) -> Optional[Dict[str, Any]]:
        print("\n" + "="*30)
        print(f"💭 Thought: {thought_msg.content[:500]}...")
        print("="*30 + "\n")
        return None

    async def on_before_action(self, state: AgentState, action: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        tool_name = action.get("tool_name", "unknown")
        arguments = action.get("arguments", {})
        self._print_header(f"TOOL CALL: {tool_name}", "\033[93m")
        print(f"🛠️ Arguments: {json.dumps(arguments, ensure_ascii=False, indent=2)}")
        return None

    async def on_after_action(self, state: AgentState, action: Dict[str, Any], result: Any) -> Optional[Dict[str, Any]]:
        tool_name = action.get("tool_name", "unknown")
        # 判断结果状态
        status = "success"
        if isinstance(result, dict) and result.get("status") == "error":
            status = "error"
        elif hasattr(result, "status") and result.status == "error":
            status = "error"

        color = "\033[92m" if status == "success" else "\033[91m"
        self._print_header(f"TOOL RESULT: {tool_name}", color)
        
        output_str = str(result)
        if len(output_str) > 1000:
             output_str = output_str[:1000] + f" ... [truncated]"
        print(f"📤 Output: {output_str}")
        return None

    async def on_error(self, state: AgentState, error: Exception) -> None:
        self._print_header(f"ERROR: {state.agent_id}", "\033[91m")
        print(f"❌ Details: {str(error)}")