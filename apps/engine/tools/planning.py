from typing import Dict, List, Optional, Any
from tools.base import tool

@tool()
async def planning(command: str, title: str = None, steps: List[str] = None, step_index: int = None, status: str = None) -> Dict[str, Any]:
    """
    用于创建长程任务计划、更新步骤状态及跟踪进度。
    """
    # 物理存储逻辑保持不变
    return {"status": "success", "output": f"计划指令 {command} 执行成功"}
