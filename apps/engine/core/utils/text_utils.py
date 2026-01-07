"""
文本处理工具集 (Text Utilities)

提供文本切分、清洗及字符处理等原子化操作，支持长上下文管理与数据预处理。
"""

import re
from typing import List

def split_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """
    执行带重叠区域的文本物理切分。
    
    Args:
        text: 目标长文本。
        chunk_size: 分片容量。
        overlap: 重叠长度。
        
    Returns:
        List[str]: 文本分片序列。
    """
    if not text:
        return []
    
    if len(text) <= chunk_size:
        return [text]
        
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
        
    return chunks

def clean_invisible_chars(text: str) -> str:
    """
    移除文本中的不可见控制字符。
    """
    return re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
