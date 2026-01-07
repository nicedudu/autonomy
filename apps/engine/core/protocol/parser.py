import re
from core.utils.json_utils import extract_json
from .schema import ProtocolResponse

class ProtocolParseError(Exception):
    """协议解析异常：载荷格式或 Schema 契约校验失败。"""
    pass

class ProtocolParser:
    """协议解析引擎。
    
    执行推理文本向执行契约的结构化转换。
    """

    @staticmethod
    def parse(text: str) -> ProtocolResponse:
        """解析协议载荷并执行契约校验。
        
        Args:
            text: 原始模型输出文本。
            
        Returns:
            ProtocolResponse: 结构化协议对象。
            
        Raises:
            ProtocolParseError: 格式不可解析或 Schema 校验不通过。
        """
        data = extract_json(text)
        
        if not isinstance(data, dict):
            raise ProtocolParseError("载荷缺失有效协议字典结构")

        try:
            return ProtocolResponse.model_validate(data)
        except Exception as e:
            raise ProtocolParseError(f"Schema 契约校验失败: {str(e)}")

    @staticmethod
    def strip_protocol(text: str) -> str:
        """剥离 Markdown 协议代码块。"""
        return re.sub(r"```json.*?```", "", text, flags=re.DOTALL).strip()
