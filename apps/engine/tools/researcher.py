import asyncio
import json
import os
from typing import Any, Dict, List
from core.llm_factory import LLMFactory
from core.prompt_manager import prompt_manager

async def run(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Asynchronous deep research tool.
    Performs query expansion, concurrent web search/fetch, and multi-source synthesis.
    """
    query = params.get("query")
    if not query:
        return {"status": "error", "message": "Missing 'query' parameter."}

    llm = LLMFactory()
    
    # Intent decomposition for multi-perspective search
    print(f"[Researcher] Expanding query: {query}")
    expand_system = prompt_manager.get_prompt("tools.researcher.expansion")
    expand_prompt = [
        {"role": "system", "content": expand_system},
        {"role": "user", "content": f"Query: {query}"}
    ]
    
    try:
        expansion_resp = llm.call_default_llm(expand_prompt)
        content = expansion_resp.content.strip()
        
        # Robust JSON extraction from LLM response
        if "[" in content and "]" in content:
            start = content.find("[")
            end = content.rfind("]") + 1
            content = content[start:end]
        
        search_queries = json.loads(content)
        if not isinstance(search_queries, list):
            search_queries = [query]
    except Exception as e:
        search_queries = [query]

    # Concurrent search execution
    from tools import web_search
    search_tasks = [web_search.run({"query": q}) for q in search_queries]
    search_results = await asyncio.gather(*search_tasks)
    
    all_urls = []
    for res in search_results:
        if res.get("status") == "success" and isinstance(res.get("output"), list):
            all_urls.extend([item["link"] for item in res["output"][:3]])
    
    unique_urls = list(set(all_urls))[:10]
    
    # Concurrent content fetching and cleaning
    from tools import web_fetch
    fetch_tasks = [web_fetch.run({"url": url}) for url in unique_urls]
    fetch_results = await asyncio.gather(*fetch_tasks)
    
    fetched_contents = []
    for res in fetch_results:
        if res.get("status") == "success":
            content_data = res.get("output", {})
            if isinstance(content_data, dict) and content_data.get("markdown"):
                fetched_contents.append(f"Source: {content_data.get('url')}\nContent: {content_data['markdown'][:3000]}")
    
    if not fetched_contents:
        return {"status": "error", "message": "No content fetched from results."}

    # Final multi-source intelligence synthesis
    print(f"[Researcher] Synthesizing report...")
    context = "\n\n---\n\n".join(fetched_contents)
    
    if len(context) > 20000:
        context = context[:20000] + "\n... (truncated)"
        
    synthesize_system = prompt_manager.get_prompt("tools.researcher.synthesis")
    synthesize_prompt = [
        {"role": "system", "content": synthesize_system},
        {"role": "user", "content": f"Query: {query}\n\nReferences:\n{context}"}
    ]
    
    try:
        final_resp = llm.call_default_llm(synthesize_prompt)
        return {
            "status": "success",
            "output": final_resp.content,
            "metadata": {
                "queries_used": search_queries,
                "urls_fetched": len(fetched_contents)
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Synthesis failed: {str(e)}"}
