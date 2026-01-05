import httpx
from bs4 import BeautifulSoup
from typing import Dict, Any
import urllib.parse
from tools.base import BaseTool

class WebFetchTool(BaseTool):
    """
    异步网页内容提取工具。
    """
    
    @property
    def name(self) -> str:
        return "web_fetch"

    @property
    def description(self) -> str:
        return "提取指定 URL 的网页内容，并将其转换为干净的 Markdown 文本。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "目标网页的完整 URL"
                }
            },
            "required": ["url"]
        }

    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        url = params.get("url", "").strip()
        if not url: return {"status": "error", "message": "URL 不能为空。"}

        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
                response = await client.get(url)
                response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            for tag in soup(["script", "style", "nav", "footer"]): tag.decompose()
            
            text = soup.get_text(separator='\n', strip=True)
            return {
                "status": "success",
                "output": f"# TITLE: {soup.title.string}\n\n{text[:6000]}"
            }
        except Exception as e:
            return {"status": "error", "message": f"提取失败: {str(e)}"}

async def run(params: Dict[str, Any]) -> Dict[str, Any]:
    return await WebFetchTool().run(params)