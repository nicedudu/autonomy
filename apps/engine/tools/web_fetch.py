import httpx
from bs4 import BeautifulSoup
from typing import Dict, Any
import urllib.parse

async def run(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    异步网页内容提取工具。
    提供专业的 HTML 清洗、降噪以及针对大语言模型优化的文本输出。
    """
    url = params.get("url", "").strip()
    if not url:
        return {"status": "error", "message": "URL 不能为空。"}

    # 安全审计
    parsed_url = urllib.parse.urlparse(url)
    if parsed_url.scheme not in ["http", "https"]:
        return {"status": "error", "message": "仅支持 HTTP 或 HTTPS 协议。"}
    
    # 防止 SSRF
    restricted_hosts = ["localhost", "127.0.0.1", "0.0.0.0"]
    if any(host in parsed_url.netloc for host in restricted_hosts):
        return {"status": "error", "message": "禁止访问内网敏感地址。"}

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,xml;q=0.9,*/*;q=0.8"
    }

    try:
        # 执行异步请求
        async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
        
        # 解析 HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. 强力降噪：删除非内容标签
        noise_tags = ["script", "style", "nav", "footer", "header", "aside", "form", "iframe", "noscript", "ads"]
        for tag in soup(noise_tags):
            tag.decompose()

        # 2. 核心内容提取
        # 优先寻找 main 或 article 标签
        main_content = soup.find("main") or soup.find("article") or soup.find("body")
        
        # 3. 提取标题与正文
        title = soup.title.string.strip() if soup.title else "未命名页面"
        
        # 转换为更具语义的纯文本
        raw_text = main_content.get_text(separator='\n', strip=True) if main_content else ""
        
        # 过滤极短的干扰项，但保留 5 字符以上的行（以捕获价格等关键数据）
        lines = [line.strip() for line in raw_text.splitlines() if len(line.strip()) > 5]
        cleaned_text = "\n".join(lines)

        # 4. 智能截断（保护上下文健康度）
        max_chars = 6000
        is_truncated = len(cleaned_text) > max_chars
        final_content = cleaned_text[:max_chars] + ("\n\n[提示：内容因过长已被截断...]" if is_truncated else "")

        return {
            "status": "success",
            "metadata": {
                "title": title,
                "url": url,
                "is_truncated": is_truncated
            },
            "output": f"# TITLE: {title}\n# URL: {url}\n\n{final_content}"
        }
    except Exception as e:
        return {"status": "error", "message": f"网页抓取失败: {str(e)}"}
