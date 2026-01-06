import asyncio
import logging
import time
import json
from typing import AsyncGenerator, Dict, List

from core.llm.client_manager import LLMClientManager
from core.llm.providers.base import ProviderResponse
from core.schema.models import LLMConfig
from core.utils.retry import RetryStrategy

logger = logging.getLogger(__name__)

class LLMService:
    """
    LLM 执行服务层。
    负责请求路由、参数解析、异常重试及上下文日志记录。
    纯粹的执行器 (Pure Executor)，不包含任何配置解析逻辑。
    """

    def __init__(self):
        self.client_manager = LLMClientManager()
        self.max_retries = 3

    async def stream(
        self,
        config: LLMConfig,
        messages: List[Dict[str, str]],
        **runtime_kwargs
    ) -> AsyncGenerator[str, None]:
        """
        执行异步流式推理。
        
        Args:
            config: 完整的 LLM 配置对象 (含连接与参数)。
            messages: OpenAI 格式的历史消息列表。
            **runtime_kwargs: 运行时动态覆盖参数 (如 stop sequences)。
            
        Yields:
            str: 实时生成的文本片段。
        """
        # 1. 准备适配器
        adapter = self.client_manager.get_adapter({
            "provider_type": config.provider,
            "api_key": config.api_key,
            "base_url": config.base_url
        })

        # 2. 组装参数 (Config 定义优先，runtime_kwargs 仅用于临时覆盖)
        final_params = {
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "top_p": config.top_p,
            **config.extra_params,
            **runtime_kwargs
        }

        self._log_request_context(config.model, final_params, messages)

        for attempt in range(self.max_retries + 1):
            try:
                async for chunk in adapter.stream(config.model, messages, **final_params):
                    yield chunk
                return
            except Exception as e:
                # 400 错误：请求非法，不可重试
                if RetryStrategy.is_invalid_request(e):
                    logger.error(f"LLM 400 Error (Invalid Request): {e}")
                    raise e
                
                # 429 错误：触发限流，执行指数退避
                if RetryStrategy.is_rate_limit(e) and attempt < self.max_retries:
                    delay = RetryStrategy.get_backoff_delay(attempt)
                    logger.warning(f"Rate limit hit ({e}), retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    continue
                
                logger.error(f"LLM Stream Failed after {attempt} retries: {e}")
                raise e

    def call(
        self,
        config: LLMConfig,
        messages: List[Dict[str, str]],
        **runtime_kwargs
    ) -> ProviderResponse:
        """
        执行同步阻塞推理。
        """
        adapter = self.client_manager.get_adapter({
            "provider_type": config.provider,
            "api_key": config.api_key,
            "base_url": config.base_url
        })

        final_params = {
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "top_p": config.top_p,
            **config.extra_params,
            **runtime_kwargs
        }

        self._log_request_context(config.model, final_params, messages)

        for attempt in range(self.max_retries + 1):
            try:
                return adapter.call(config.model, messages, **final_params)
            except Exception as e:
                if RetryStrategy.is_invalid_request(e):
                     logger.error(f"LLM 400 Error: {e}")
                     raise e

                if RetryStrategy.is_rate_limit(e) and attempt < self.max_retries:
                    delay = RetryStrategy.get_backoff_delay(attempt)
                    logger.warning(f"Rate limit hit, retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                raise e

    def _log_request_context(self, model: str, params: Dict, messages: List[Dict]):
        """输出开发环境调试日志 (Stdout)。"""
        try:
            print(f"\n[LLM Request] Model: {model}")
            print(f"[LLM Params] {json.dumps(params, ensure_ascii=False)}")
            last_msg = messages[-1] if messages else {}
            print(f"[LLM Context] Last Msg: {str(last_msg.get('content'))[:100]}...")
        except Exception:
            pass
