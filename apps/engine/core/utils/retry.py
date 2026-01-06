import logging

logger = logging.getLogger(__name__)


class RetryStrategy:
    """
    通用重试策略组件。
    支持指数退避与特定异常过滤。
    """

    @staticmethod
    def get_backoff_delay(attempt: int, base: float = 2.0) -> float:
        """计算指数退避延迟时间。"""
        return base * (2 ** attempt)

    @staticmethod
    def is_rate_limit(error: Exception) -> bool:
        """
        判断是否为限流类错误。
        支持 OpenAI/Anthropic SDK 异常及标准 HTTP 429 状态码。
        """
        error_str = str(error).lower()
        if "rate limit" in error_str or "429" in error_str:
            return True

        # 检查对象属性
        if getattr(error, "status_code", None) == 429:
            return True

        return False

    @staticmethod
    def is_context_window_exceeded(error: Exception) -> bool:
        """判断是否为上下文溢出错误 (400/Bad Request 的一种常见情况)。"""
        error_str = str(error).lower()
        return "context_length_exceeded" in error_str or "token limit" in error_str

    @staticmethod
    def is_invalid_request(error: Exception) -> bool:
        """判断是否为无效请求 (400)。"""
        if getattr(error, "status_code", None) == 400:
            return True
        return False
