import asyncio
from typing import Dict, Any, Optional
from tools.base import tool

@tool()
async def web_search(query: str, provider: Optional[str] = "duckduckgo") -> Dict[str, Any]:
    """
    实时互联网搜索，用于获取最新的事实、数据、汇率或新闻信息。
    
    Args:
        query: 具体的搜索关键词。
        provider: 指定搜索引擎供应商（duckduckgo/tavily/google）。
    """
    print(f"[WebSearch] 正在搜索: {query} (Provider: {provider})")
    
    # 实际执行逻辑...
    from ddgs import DDGS
    try:
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, lambda: list(DDGS().text(query, max_results=5)))
        formatted = [f"[{i+1}] {r['title']}\nURL: {r['href']}\n" for i, r in enumerate(results)]
        return {"status": "success", "output": "\n".join(formatted)}
    except Exception as e:
        return {"status": "error", "message": str(e)}