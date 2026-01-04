import os
import httpx
import asyncio
from typing import Dict, Any, List

class SearchProvider:
    async def search(self, query: str) -> Dict[str, Any]:
        raise NotImplementedError

class DuckDuckGoProvider(SearchProvider):
    """Production-grade DuckDuckGo Search Provider (Free)"""
    async def search(self, query: str) -> Dict[str, Any]:
        try:
            # Note: ddgs library might be blocking, but we wrap it for interface consistency.
            # In production, we'd use an async-native search API if available.
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
                sources.append({"title": title, "link": link}) # Changed link key to align with researcher.py expectations
            
            return {"status": "success", "output": "\n".join(formatted), "sources": sources}
        except Exception as e:
            return {"status": "error", "message": f"DDGS execution failed: {str(e)}"}

class GoogleSerperProvider(SearchProvider):
    """Google (Serper) Search Provider (Paid)"""
    async def search(self, query: str) -> Dict[str, Any]:
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            return {"status": "error", "message": "SERPER_API_KEY not configured."}
        
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
            return {"status": "error", "message": f"Google search failed: {str(e)}"}

class TavilyProvider(SearchProvider):
    """Tavily Search Provider (AI-Optimized)"""
    async def search(self, query: str) -> Dict[str, Any]:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return {"status": "error", "message": "TAVILY_API_KEY not configured."}
        
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
            return {"status": "error", "message": f"Tavily search failed: {str(e)}"}

async def run(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Asynchronous Intelligent Web Search Engine.
    """
    query = params.get("query", "").strip()
    if not query:
        return {"status": "error", "message": "Query cannot be empty."}

    explicit_provider = params.get("provider", "").lower()
    available_providers = {"duckduckgo": DuckDuckGoProvider()}
    
    if os.getenv("SERPER_API_KEY"): available_providers["google"] = GoogleSerperProvider()
    if os.getenv("TAVILY_API_KEY"): available_providers["tavily"] = TavilyProvider()

    if explicit_provider in available_providers:
        provider_name = explicit_provider
    elif "tavily" in available_providers:
        provider_name = "tavily"
    elif "google" in available_providers:
        provider_name = "google"
    else:
        provider_name = "duckduckgo"

    print(f"[WebSearch] Executing search via {provider_name}")
    
    result = await available_providers[provider_name].search(query)
    
    if result.get("status") == "success":
        result["output"] += "\n\nNote: Use 'web_fetch' with the URL for full context."
    
    return result
