import re
import json
from typing import List, Dict, Any, Optional
from core.protocol.schema import ProtocolResponse, ProtocolAction, ProtocolCall

class ProtocolParser:
    """
    协议解析器。
    采用正则与状态机结合的方式，从 LLM 响应中提取结构化 XML 块。
    """

    @staticmethod
    def parse(text: str) -> ProtocolResponse:
        """
        全量解析 LLM 输出文本。
        """
        response = ProtocolResponse()

        # 1. 提取思考内容 (Thought)
        response.thought = ProtocolParser._extract_tag(text, "thought")

        # 2. 提取反思 (Reflection)
        response.reflection = ProtocolParser._extract_tag(text, "reflection")

        # 3. 提取结论 (Conclusion)
        response.conclusion = ProtocolParser._extract_tag(text, "conclusion")

        # 4. 解析行动 (Actions - JSON inside XML)
        action_blocks = ProtocolParser._extract_all_tags(text, "action")
        for block in action_blocks:
            try:
                data = json.loads(block.strip())
                response.actions.append(ProtocolAction(
                    tool_name=data.get("tool_name"),
                    arguments=data.get("arguments", {})
                ))
            except json.JSONDecodeError:
                pass

        # 5. 解析协作 (Calls)
        call_blocks = ProtocolParser._extract_all_tags(text, "call")
        for block in call_blocks:
            try:
                data = json.loads(block.strip())
                response.calls.append(ProtocolCall(
                    target_id=data.get("target_id"),
                    task=data.get("task"),
                    context=data.get("context", {})
                ))
            except json.JSONDecodeError:
                pass

        return response

    @staticmethod
    def _extract_tag(text: str, tag: str) -> Optional[str]:
        """提取单个标签的内容 (最新优先)"""
        pattern = f"<{tag}>(.*?)</{tag}>"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else None

    @staticmethod
    def _extract_all_tags(text: str, tag: str) -> List[str]:
        """提取所有同名标签的内容"""
        pattern = f"<{tag}>(.*?)</{tag}>"
        return re.findall(pattern, text, re.DOTALL)

    @staticmethod
    def clean_text(text: str) -> str:
        """
        移除文本中的所有协议标签，只保留原始会话文本。
        """
        return re.sub(r"<(thought|action|call|reflection|plan|artifact)>.*?</\1>", "", text, flags=re.DOTALL).strip()
