import asyncio
from typing import Dict, Any, Optional
from core.tools.base import tool

@tool()
async def web_search(query: str, provider: Optional[str] = "duckduckgo") -> Dict[str, Any]:
    """
    搜索互联网实时信息。
    
    Args:
        query: 具体的搜索关键词。
        provider: 搜索供应商。
    """
    from ddgs import DDGS
    try:
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, lambda: list(DDGS().text(query, max_results=5)))
        formatted = [f"[{i+1}] {r['title']}\nURL: {r['href']}\n" for i, r in enumerate(results)]
        return {"status": "success", "output": "\n".join(formatted)}
    except Exception as e:
        return {"status": "error", "message": str(e)}