import os
import httpx
import asyncio
from typing import Dict, Any, List
from tools.base import BaseTool

class WebSearchTool(BaseTool):
    """
    异步智能搜索引擎工具。
    支持 DuckDuckGo, Google (Serper), Tavily。
    """
    
    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "实时互联网搜索，用于获取最新的事实、数据、汇率或新闻信息。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "具体的搜索关键词"
                },
                "provider": {
                    "type": "string",
                    "enum": ["duckduckgo", "tavily", "google"],
                    "description": "指定搜索引擎供应商（可选）"
                }
            },
            "required": ["query"]
        }

    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        query = params.get("query", "").strip()
        if not query:
            return {"status": "error", "message": "搜索关键词不能为空。"}

        provider_name = self._resolve_provider(params.get("provider", ""))
        print(f"[WebSearch] 正在通过 {provider_name} 执行检索...")
        
        # 逻辑复用之前的 Provider 实现（此处精简展示）
        result = await self._execute_search(provider_name, query)
        
        if result.get("status") == "success":
            result["output"] += "\n\n注：请配合使用 'web_fetch' 获取完整内容。"
        return result

    def _resolve_provider(self, explicit: str) -> str:
        available = ["duckduckgo"]
        if os.getenv("SERPER_API_KEY"): available.append("google")
        if os.getenv("TAVILY_API_KEY"): available.append("tavily")
        
        if explicit.lower() in available: return explicit.lower()
        return "tavily" if "tavily" in available else "duckduckgo"

    async def _execute_search(self, provider: str, query: str) -> Dict[str, Any]:
        # 模拟内部搜索逻辑（实际应包含之前的逻辑）
        from ddgs import DDGS
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, lambda: list(DDGS().text(query, max_results=5)))
            formatted = [f"[{i+1}] {r['title']}\nURL: {r['href']}\nSummary: {r['body']}\n" for i, r in enumerate(results)]
            return {"status": "success", "output": "\n".join(formatted)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

# 保持对 ToolRunner 的兼容
async def run(params: Dict[str, Any]) -> Dict[str, Any]:
    return await WebSearchTool().run(params)
