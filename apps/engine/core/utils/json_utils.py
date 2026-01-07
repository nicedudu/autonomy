import json
import re
from typing import Optional, Union
from json_repair import repair_json

def extract_json(text: str) -> Optional[Union[dict, list]]:
    """阶梯式 JSON 提取器。
    
    层级逻辑：1. Markdown 块预处理；2. RFC 8259 标准解析；3. 启发式语法修复。
    
    Args:
        text: 包含潜在载荷的原始文本。
        
    Returns:
        Optional[Union[dict, list]]: 结构化数据或 None。
    """
    if not text:
        return None

    content = text.strip()
    if "```" in content:
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL)
        if match:
            content = match.group(1).strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    try:
        result = repair_json(content, return_objects=True)
        return result if isinstance(result, (dict, list)) else None
    except Exception:
        return None
