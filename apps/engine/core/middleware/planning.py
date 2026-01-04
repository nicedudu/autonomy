import re
from typing import List, Dict
from core.middleware.base import AgentMiddleware
from core.schema.models import ActionCall, ActionResult

class PlanningMiddleware(AgentMiddleware):
    """
    规划同步中间件 (Active State Synchronization).
    
    功能：
    1. 监听 Agent 的思考过程 (<thought>...<plan>...</plan>).
    2. 如果检测到 <plan> 标签，自动解析其内容。
    3. 调用 PlanningTool.sync_from_markdown() 实时更新后端状态。
    
    价值：
    解决 Agent "只说不做"（只输出文本计划但不调用工具）的常见问题，
    确保 System Prompt 中的 [Live Plan State] 永远是最新的。
    """
    
    def __init__(self):
        self.plan_pattern = re.compile(r"<plan>(.*?)</plan>", re.DOTALL)

    async def on_after_think(self, agent_id: str, response: str) -> str:
        """
        在 Agent 思考完成后，立即通过中间件“旁路”提取并同步计划。
        这不会干扰 Agent 原本的 Tool Call 逻辑，而是作为一种保障机制。
        """
        match = self.plan_pattern.search(response)
        if match:
            plan_content = match.group(1).strip()
            if plan_content:
                try:
                    # 动态导入以避免循环依赖
                    from tools.planning import PlanningTool
                    tool = PlanningTool()
                    tool.sync_from_markdown(plan_content)
                    # print(f"[PlanningMiddleware] ✅ 已将思维链中的计划自动同步至状态库。")
                except Exception as e:
                    print(f"[PlanningMiddleware] ⚠️ 自动同步计划失败: {e}")
        
        return response

    # 其他钩子保持默认即可，我们主要关注 on_after_think 的副作用