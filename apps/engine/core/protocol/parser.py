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

class ProtocolStreamFilter:
    """
    流式协议过滤器。
    在 LLM 输出过程中实时过滤掉技术标签，仅保留允许展示给用户的内容。
    支持标签透传以便前端解析器二次处理。
    """
    def __init__(self):
        # 允许流向前端的标签
        self.allowed_tags = ["thought", "interaction", "conclusion"]
        self.buffer = ""
        self.current_tag = None
        self.tag_pattern = re.compile(r"<(/?)\s*(\w+)\s*>")

    def parse_chunk(self, chunk: str) -> str:
        """
        处理新的数据块，返回应发送给前端的文本。
        """
        self.buffer += chunk
        output = ""
        
        while True:
            match = self.tag_pattern.search(self.buffer)
            if not match:
                # 如果没有发现完整标签，且当前在允许的标签内，则尝试输出
                if self.current_tag in self.allowed_tags:
                    # 保留末尾防止标签截断
                    safe_len = max(0, len(self.buffer) - 15)
                    if safe_len > 0:
                        output += self.buffer[:safe_len]
                        self.buffer = self.buffer[safe_len:]
                elif self.current_tag is not None:
                    # 如果当前在禁止的标签内，直接清空 buffer（除了可能的标签前缀）
                    # 查找最后一个 '<'
                    last_lt = self.buffer.lastIndexOf('<') if hasattr(self.buffer, 'lastIndexOf') else self.buffer.rfind('<')
                    if last_lt != -1:
                        self.buffer = self.buffer[last_lt:]
                    else:
                        self.buffer = ""
                break
            
            tag_start = match.start()
            is_closing = match.group(1) == "/"
            tag_name = match.group(2).lower()
            
            # 处理标签前的内容
            pre_text = self.buffer[:tag_start]
            if self.current_tag in self.allowed_tags:
                output += pre_text
            
            # 状态转换
            full_tag = match.group(0)
            if is_closing:
                if tag_name == self.current_tag:
                    if tag_name in self.allowed_tags:
                        output += full_tag
                    self.current_tag = None
            else:
                self.current_tag = tag_name
                if tag_name in self.allowed_tags:
                    output += full_tag
            
            # 消耗已处理内容
            self.buffer = self.buffer[match.end():]
            
        return output

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