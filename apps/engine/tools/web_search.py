import os
import httpx
import asyncio
from typing import Dict, Any, List

class SearchProvider:
    """搜索供应商基类。"""
    async def search(self, query: str) -> Dict[str, Any]:
        raise NotImplementedError

class DuckDuckGoProvider(SearchProvider):
    """
    DuckDuckGo 搜索驱动 (免费)。
    """
    async def search(self, query: str) -> Dict[str, Any]:
        try:
            from ddgs import DDGS
            def sync_search():
                with DDGS() as ddgs:
                    return list(ddgs.text(query, max_results=10))
            
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, sync_search)
            
            formatted = []
            sources = []
            for idx, r in enumerate(results[:5]):
                title = r.get("title", "No Title")
                link = r.get("href", r.get("link", "#"))
                snippet = r.get("body", r.get("snippet", ""))
                formatted.append(f"[{idx+1}] {title}\nURL: {link}\nSummary: {snippet}\n")
                sources.append({"title": title, "link": link})
            
            return {"status": "success", "output": "\n".join(formatted), "sources": sources}
        except Exception as e:
            return {"status": "error", "message": f"DDGS 搜索失败: {str(e)}"}

class GoogleSerperProvider(SearchProvider):
    """
    Google (Serper) 搜索驱动 (付费)。
    """
    async def search(self, query: str) -> Dict[str, Any]:
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            return {"status": "error", "message": "未配置 SERPER_API_KEY。"}
        
        url = "https://google.serper.dev/search"
        headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json={"q": query}, timeout=15)
                response.raise_for_status()
                organic = response.json().get("organic", [])
            
            formatted = []
            sources = []
            for idx, item in enumerate(organic[:5]):
                title = item.get("title", "Untitled")
                link = item.get("link", "#")
                snippet = item.get("snippet", "")
                formatted.append(f"[{idx+1}] {title}\nURL: {link}\nSummary: {snippet}\n")
                sources.append({"title": title, "link": link})
            
            return {"status": "success", "output": "\n".join(formatted), "sources": sources}
        except Exception as e:
            return {"status": "error", "message": f"Google 搜索失败: {str(e)}"}

class TavilyProvider(SearchProvider):
    """
    Tavily 搜索驱动 (AI 专用)。
    """
    async def search(self, query: str) -> Dict[str, Any]:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return {"status": "error", "message": "未配置 TAVILY_API_KEY。"}
        
        url = "https://api.tavily.com/search"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json={
                    "api_key": api_key,
                    "query": query,
                    "max_results": 5
                }, timeout=15)
                response.raise_for_status()
                results = response.json().get("results", [])
            
            formatted = []
            sources = []
            for idx, item in enumerate(results):
                title = item.get("title", "Untitled")
                link = item.get("url", "#")
                content = item.get("content", "")
                formatted.append(f"[{idx+1}] {title}\nURL: {link}\nSummary: {content}\n")
                sources.append({"title": title, "link": link})
            
            return {"status": "success", "output": "\n".join(formatted), "sources": sources}
        except Exception as e:
            return {"status": "error", "message": f"Tavily 搜索失败: {str(e)}"}

async def run(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    异步智能搜索引擎。
    支持按需切换不同的搜索服务商。
    """
    query = params.get("query", "").strip()
    if not query:
        return {"status": "error", "message": "搜索关键词不能为空。"}

    explicit_provider = params.get("provider", "").lower()
    available_providers = {"duckduckgo": DuckDuckGoProvider()}
    
    # 动态探测可用商
    if os.getenv("SERPER_API_KEY"): available_providers["google"] = GoogleSerperProvider()
    if os.getenv("TAVILY_API_KEY"): available_providers["tavily"] = TavilyProvider()

    # 路由选择逻辑
    if explicit_provider in available_providers:
        provider_name = explicit_provider
    elif "tavily" in available_providers:
        provider_name = "tavily"
    elif "google" in available_providers:
        provider_name = "google"
    else:
        provider_name = "duckduckgo"

    print(f"[WebSearch] 正在通过 {provider_name} 执行检索...")
    
    result = await available_providers[provider_name].search(query)
    
    if result.get("status") == "success":
        result["output"] += "\n\n注：请配合使用 'web_fetch' 获取完整内容。"
    
    return result