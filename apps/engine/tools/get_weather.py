import asyncio
from typing import Any, Dict
from core.llm_factory import LLMFactory
from core.prompt_manager import prompt_manager

async def run(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Weather information retrieval tool.
    Uses optimized web search to fetch real-time weather data.
    """
    location = params.get("location")
    date = params.get("date", "today")
    
    if not location:
        return {"status": "failed", "message": "Missing 'location' parameter."}

    # Use web_search to find weather info
    from tools import web_search
    search_query = f"{location} weather {date}"
    
    try:
        search_result = await web_search.run({"query": search_query})
        if search_result.get("status") == "success":
            return {
                "status": "success",
                "output": search_result.get("output"),
                "location": location,
                "date": date
            }
        else:
            return {"status": "failed", "message": "Could not retrieve weather data via search."}
    except Exception as e:
        return {"status": "failed", "message": f"Weather tool error: {str(e)}"}
