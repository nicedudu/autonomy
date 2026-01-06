import httpx
from bs4 import BeautifulSoup
from typing import Dict, Any
from tools.base import tool

@tool()
async def web_fetch(url: str) -> Dict[str, Any]:
    """
    爬取网页纯文本内容。
    
    Args:
        url: 目标网页链接。
    """
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
            response = await client.get(url)
            response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for tag in soup(["script", "style"]): tag.decompose()
        return {
            "status": "success",
            "output": f"# TITLE: {soup.title.string}\n\n{soup.get_text(separator='\n', strip=True)[:6000]}"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

