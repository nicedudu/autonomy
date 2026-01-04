from typing import List, Dict, Optional
from core.middleware.base import AgentMiddleware

class StuckLoopMiddleware(AgentMiddleware):
    """
    循环检测中间件 (Observer Mode).
    仅负责检测并记录重复状态，不直接修改用户输入。
    """
    
    def __init__(self, threshold: int = 3):
        self.threshold = threshold
        self.history_hashes: List[int] = []

    async def on_startup(self, agent_id: str, prompt: str):
        self.history_hashes.clear()

    async def on_after_think(self, agent_id: str, response: str) -> str:
        content_hash = hash(response.strip())
        self.history_hashes.append(content_hash)
        if len(self.history_hashes) > self.threshold * 2:
            self.history_hashes.pop(0)
        return response

    async def on_before_think(self, agent_id: str, history: List[Dict]) -> Optional[List[Dict]]:
        # 检测是否卡死
        if len(self.history_hashes) >= self.threshold:
            recent_hashes = self.history_hashes[-self.threshold:]
            if len(set(recent_hashes)) == 1:
                # 仅打印日志，不修改历史
                print(f"\033[93m[HealthCheck] ⚠️ Warning: Agent produced identical outputs for last {self.threshold} turns.\033[0m")
                
                # 可选：如果需要，可以在这里返回一个增加了一条 System Hint 的新 history
                # new_history = history.copy()
                # new_history.append({"role": "system", "content": "[Context Hint: Previous actions seem repetitive. Consider a new strategy.]"})
                # return new_history
        
        return None