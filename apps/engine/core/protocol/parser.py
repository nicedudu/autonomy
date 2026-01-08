import re
import json
from typing import Optional, List, Dict, Any
from core.utils.json_utils import extract_json
from .schema import ProtocolResponse, PlanStep, ProtocolCall

class ProtocolParseError(Exception):
    """协议解析异常：载荷格式或 Schema 契约校验失败。"""
    pass

class ProtocolParser:
    """协议解析引擎 (Mixed-Format Protocol)。
    
    解析包含 XML 标签 (<thought>, <plan>, <calls>) 和自然语言的混合流。
    """

    @staticmethod
    def parse(text: str) -> ProtocolResponse:
        """解析混合协议载荷。
        
        Args:
            text: 原始模型输出文本。
            
        Returns:
            ProtocolResponse: 结构化协议对象。
        """
        response = ProtocolResponse()
        
        # 1. Extract Thought
        thought_match = re.search(r"<thought>(.*?)</thought>", text, re.DOTALL)
        if thought_match:
            response.thought = thought_match.group(1).strip()
            # Remove thought from text to avoid duplication in content
            text = text.replace(thought_match.group(0), "")

        # 2. Extract Plan
        plan_match = re.search(r"<plan>(.*?)</plan>", text, re.DOTALL)
        if plan_match:
            plan_content = plan_match.group(1).strip()
            try:
                # Handle potential markdown code blocks inside tags
                plan_data = extract_json(plan_content)
                if isinstance(plan_data, list):
                    response.plan = [PlanStep.model_validate(item) for item in plan_data]
            except Exception as e:
                # Log warning but don't fail the whole parse? 
                # For strict protocol, maybe we should fail.
                pass
            text = text.replace(plan_match.group(0), "")

        # 3. Extract Calls
        calls_match = re.search(r"<calls>(.*?)</calls>", text, re.DOTALL)
        if calls_match:
            calls_content = calls_match.group(1).strip()
            try:
                calls_data = extract_json(calls_content)
                # Support {"calls": [...]} or just [...]
                if isinstance(calls_data, dict) and "calls" in calls_data:
                    calls_list = calls_data["calls"]
                elif isinstance(calls_data, list):
                    calls_list = calls_data
                else:
                    calls_list = []
                
                response.calls = [ProtocolCall.model_validate(item) for item in calls_list]
            except Exception:
                pass
            text = text.replace(calls_match.group(0), "")

        # 3.1 Extract Tool Calls
        tool_calls_match = re.search(r"<tool_calls>(.*?)</tool_calls>", text, re.DOTALL)
        if tool_calls_match:
            tool_calls_content = tool_calls_match.group(1).strip()
            try:
                tool_calls_data = extract_json(tool_calls_content)
                if isinstance(tool_calls_data, list):
                    response.tool_calls = [ProtocolAction.model_validate(item) for item in tool_calls_data]
            except Exception:
                pass
            text = text.replace(tool_calls_match.group(0), "")

        # 4. Extract Metadata (Optional, mostly for removal)
        metadata_match = re.search(r"<metadata>(.*?)</metadata>", text, re.DOTALL)
        if metadata_match:
            text = text.replace(metadata_match.group(0), "")

        # 5. Remaining text is Content
        response.content = text.strip()
        
        # Fallback: if empty content but thought exists, maybe just return.
        
        return response

    @staticmethod
    def strip_protocol(text: str) -> str:
        """移除所有协议标签，仅保留自然语言内容。"""
        # 使用 count=0 (默认) 确保移除所有匹配项
        clean_text = re.sub(r"<thought>.*?</thought>", "", text, flags=re.DOTALL)
        clean_text = re.sub(r"<plan>.*?</plan>", "", clean_text, flags=re.DOTALL)
        clean_text = re.sub(r"<calls>.*?</calls>", "", clean_text, flags=re.DOTALL)
        clean_text = re.sub(r"<tool_calls>.*?</tool_calls>", "", clean_text, flags=re.DOTALL)
        clean_text = re.sub(r"<metadata>.*?</metadata>", "", clean_text, flags=re.DOTALL)
        return clean_text.strip()