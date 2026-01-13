"""
互联网能力插件 (Internet Capability)

集成全球信息检索与深度内容提取功能。
"""

import asyncio
from typing import Any, Dict

import httpx
from bs4 import BeautifulSoup
from core.tools.base import tool


@tool()
async def search_internet(query: str, count: int = 5) -> Dict[str, Any]:
    """
    通过搜索引擎检索互联网实时信息。
    支持获取最新新闻、事实性考据及技术文档摘要。

    Args:
        query: 检索关键词。
        count: 返回结果的最大数量（默认 5）。
    """
    from ddgs import DDGS
    try:
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: list(DDGS().text(query, max_results=count))
        )
        return {
            "status": "success",
            "query": query,
            "results": [
                {"title": r.get("title"), "link": r.get(
                    "href"), "snippet": r.get("body")}
                for r in results
            ]
        }
    except Exception as e:
        return {"status": "error", "message": f"搜索引擎连接失败: {str(e)}"}


@tool()
async def fetch_web_page(url: str) -> Dict[str, Any]:
    """
    深度抓取并解析指定网页的正文内容。
    实现自动降噪，剔除广告与导航，提取对 LLM 有用的核心信息。

    Args:
        url: 网页的完整 URL 地址。
    """
    headers = {"User-Agent": "AutonomyEngine/1.0 (Enterprise Bot)"}
    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
        try:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()

            text = soup.get_text(separator="\n")
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            final_text = "\n".join(lines)

            return {
                "status": "success",
                "url": url,
                "content": final_text[:12000],  # 截断以防止上下文溢出
                "is_truncated": len(final_text) > 12000
            }
        except Exception as e:
            return {"status": "error", "message": f"抓取网页失败: {str(e)}"}
