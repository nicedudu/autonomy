"""
V4.0 协议解析引擎 (Protocol Parsing Engine)
"""

import re
import json
import logging
from typing import Optional, List, Dict, Any, Type, TypeVar, Union
from pydantic import BaseModel, ValidationError

from core.utils.json_utils import extract_json
from core.schema.orchestration import WorkflowManifest, DispatchItem
from core.protocol.schema import ProtocolResponse, ProtocolReflection

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

class ProtocolParser:
    """
    V4.0 编排协议解析器。
    """

    @staticmethod
    def parse(text: str) -> ProtocolResponse:
        """
        全量解析输入报文，并记录所有契约违约点。
        """
        response = ProtocolResponse(raw_payload=text)
        
        # 1. 提取基础标签
        response.thought = ProtocolParser._extract_tag(text, "thought")
        response.interaction = ProtocolParser._extract_tag(text, "interaction")
        response.conclusion = ProtocolParser._extract_tag(text, "conclusion")
        
        # 2. 解析蓝图 (Blueprint)
        blueprint_raw = ProtocolParser._extract_tag(text, "blueprint")
        if blueprint_raw:
            try:
                data = extract_json(blueprint_raw)
                if data:
                    response.blueprint = WorkflowManifest.model_validate(data)
            except Exception as e:
                response.errors.append(f"[Blueprint 解析失败] 结构不符合契约: {str(e)}")

        # 3. 解析派发项 (Dispatch)
        dispatch_raw = ProtocolParser._extract_tag(text, "dispatch")
        if dispatch_raw:
            try:
                data = extract_json(dispatch_raw)
                if isinstance(data, list):
                    for idx, item in enumerate(data):
                        try:
                            response.dispatch.append(DispatchItem.model_validate(item))
                        except Exception as e:
                            response.errors.append(f"[Dispatch 项 {idx} 校验失败] 字段缺失或类型错误: {str(e)}")
                else:
                    response.errors.append("[Dispatch 格式错误] 内容必须是一个 JSON 列表。")
            except Exception as e:
                response.errors.append(f"[Dispatch 解析失败] 无法提取合法的 JSON: {str(e)}")

        return response

    @staticmethod
    def _extract_tag(text: str, tag: str) -> Optional[str]:
        pattern = rf"<\s*{tag}\s*>(.*?)</\s*{tag}\s*>"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            content = match.group(1).strip()
            json_block = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL | re.IGNORECASE)
            return json_block.group(1).strip() if json_block else content
        return None

    @staticmethod
    def strip_protocol(text: str) -> str:
        res = ProtocolParser.parse(text)
        parts = []
        if res.interaction: parts.append(res.interaction)
        if res.conclusion: parts.append(res.conclusion)
        return "\n\n".join(parts)