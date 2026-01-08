import httpx
from bs4 import BeautifulSoup
from core.tools.base import tool

@tool(
    name="web_fetch",
    description="深度抓取指定 URL 的网页内容。返回经过清理的结构化正文，适用于精读与数据提取。",
    parameters={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "目标网页的完整 URL"}
        },
        "required": ["url"]
    }
)
async def web_fetch(url: str) -> str:
    """抓取网页并执行深度降噪处理。"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            # --- 生产级降噪逻辑 ---
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 1. 移除干扰标签
            for script_or_style in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
                script_or_style.decompose()
            
            # 2. 提取文本并清理空白
            text = soup.get_text(separator="\n")
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            
            # 3. 截断极长内容以保护上下文窗口 (Max 15000 chars)
            cleaned_content = "\n".join(lines)
            return cleaned_content[:15000]
            
        except Exception as e:
            return f"网页抓取失败: {str(e)}"