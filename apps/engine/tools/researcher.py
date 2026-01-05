from typing import Any, Dict
from tools.base import tool

@tool()
async def researcher(query: str) -> Dict[str, Any]:
    """
    深度调研专家。
    
    Args:
        query: 主题。
    """
    return {"status": "success", "output": "分析报告..."}

async def run(params: Dict[str, Any]) -> Dict[str, Any]:
    """兼容旧版调用。"""
    return await researcher(**params)