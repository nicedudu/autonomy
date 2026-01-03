import requests
from bs4 import BeautifulSoup
from typing import Dict, Any
import urllib.parse

def run(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhanced Web Fetch Skill (Nexus V4 Standard)
    Extracts core content from a URL with noise filtering.
    """
    url = params.get("url", "").strip()
    if not url:
        return {"status": "error", "message": "URL cannot be empty."}

    # SSRF & Safety: Basic check
    parsed_url = urllib.parse.urlparse(url)
    if parsed_url.scheme not in ["http", "https"]:
        return {"status": "error", "message": "Only HTTP and HTTPS protocols are allowed."}
    
    # Avoid local network access
    if any(host in parsed_url.netloc for host in ["localhost", "127.0.0.1", "0.0.0.0"]):
        return {"status": "error", "message": "Access to local network is restricted."}

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5,zh-CN;q=0.3"
    }

    try:
        response = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
        response.raise_for_status()
        
        # Auto-detect encoding
        if response.encoding == 'ISO-8859-1':
            response.encoding = response.apparent_encoding

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Noise Filtering
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe"]):
            tag.decompose()

        # Metadata extraction
        title = soup.title.string.strip() if soup.title else "Untitled Page"
        
        # Get core text
        # Using a simplistic approach to find the largest text container
        text = soup.get_text(separator='\n', strip=True)
        
        # Cleaning: Remove excessive empty lines
        lines = [line.strip() for line in text.splitlines() if len(line.strip()) > 10]
        cleaned_text = "\n".join(lines)

        # Truncation: Maintain context window health (Target: 5000 characters)
        max_chars = 5000
        truncated = len(cleaned_text) > max_chars
        content = cleaned_text[:max_chars] + ("\n\n[Content Truncated...]" if truncated else "")

        return {
            "status": "success",
            "metadata": {
                "title": title,
                "url": url,
                "content_length": len(cleaned_text),
                "is_truncated": truncated
            },
            "output": f"TITLE: {title}\nURL: {url}\n\nCONTENT:\n{content}"
        }
    except Exception as e:
        return {"status": "error", "message": f"Fetch failed: {str(e)}"}
