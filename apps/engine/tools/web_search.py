import os
import requests
import json
from typing import Dict, Any, List

class SearchProvider:
    def search(self, query: str) -> Dict[str, Any]:
        raise NotImplementedError

class DuckDuckGoProvider(SearchProvider):
    """Production-grade DuckDuckGo Search Provider (Free)"""
    def search(self, query: str) -> Dict[str, Any]:
        try:
            from ddgs import DDGS
            ddgs = DDGS()
            raw_gen = ddgs.text(query, max_results=10)
            results = list(raw_gen)
            
            formatted = []
            sources = []
            for idx, r in enumerate(results[:5]):
                title = r.get("title", "No Title")
                link = r.get("href", r.get("link", "#"))
                snippet = r.get("body", r.get("snippet", ""))
                formatted.append(f"[{idx+1}] {title}\nURL: {link}\nSummary: {snippet}\n")
                sources.append({"title": title, "url": link})
            
            return {"status": "success", "output": "\n".join(formatted), "sources": sources}
        except Exception as e:
            return {"status": "error", "message": f"DDGS execution failed: {str(e)}"}

class GoogleSerperProvider(SearchProvider):
    """Google (Serper) Search Provider (Paid)"""
    def search(self, query: str) -> Dict[str, Any]:
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            return {"status": "error", "message": "SERPER_API_KEY not configured."}
        
        url = "https://google.serper.dev/search"
        headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
        try:
            response = requests.post(url, headers=headers, json={"q": query}, timeout=15)
            response.raise_for_status()
            organic = response.json().get("organic", [])
            
            formatted = []
            sources = []
            for idx, item in enumerate(organic[:5]):
                title = item.get("title", "Untitled")
                link = item.get("link", "#")
                snippet = item.get("snippet", "")
                formatted.append(f"[{idx+1}] {title}\nURL: {link}\nSummary: {snippet}\n")
                sources.append({"title": title, "url": link})
            
            return {"status": "success", "output": "\n".join(formatted), "sources": sources}
        except Exception as e:
            return {"status": "error", "message": f"Google search failed: {str(e)}"}

class TavilyProvider(SearchProvider):
    """Tavily Search Provider (AI-Optimized)"""
    def search(self, query: str) -> Dict[str, Any]:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return {"status": "error", "message": "TAVILY_API_KEY not configured."}
        
        url = "https://api.tavily.com/search"
        try:
            response = requests.post(url, json={
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
                sources.append({"title": title, "url": link})
            
            return {"status": "success", "output": "\n".join(formatted), "sources": sources}
        except Exception as e:
            return {"status": "error", "message": f"Tavily search failed: {str(e)}"}

def run(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Intelligent Web Search Engine (Nexus V4)
    Automatically selects the best available provider.
    """
    query = params.get("query", "").strip()
    if not query:
        return {"status": "error", "message": "Query cannot be empty."}

    # 1. Determine Provider Priority
    # User Explicit > Configured Paid > Default Free
    explicit_provider = params.get("provider", "").lower()
    
    available_providers = {
        "duckduckgo": DuckDuckGoProvider()
    }
    
    # Register paid providers if keys are present
    if os.getenv("SERPER_API_KEY"):
        available_providers["google"] = GoogleSerperProvider()
    if os.getenv("TAVILY_API_KEY"):
        available_providers["tavily"] = TavilyProvider()

    # 2. Select Logic
    if explicit_provider in available_providers:
        provider_name = explicit_provider
    elif "tavily" in available_providers:
        provider_name = "tavily"
    elif "google" in available_providers:
        provider_name = "google"
    else:
        provider_name = "duckduckgo"

    print(f"\n🚀 [ACTUAL_TOOL_EXECUTION] Starting web_search via {provider_name}")
    
    result = available_providers[provider_name].search(query)
    
    if result["status"] == "success":
        result["output"] += "\n\nNote: To get the full context of any source above, please use the 'web_fetch' tool with the URL."
    
    return result