import os
import asyncio
from typing import Any, Dict, List

from anthropic import Anthropic, AsyncAnthropic, RateLimitError as AnthropicRateLimitError
from core.supabase_manager import SupabaseManager
from openai import OpenAI, AsyncOpenAI, RateLimitError as OpenAIRateLimitError
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, AsyncRetrying

# 定义生产级重试规则：处理限流 (429) 和 基础网络错误
RETRY_CONFIG = {
    "stop": stop_after_attempt(3),
    "wait": wait_exponential(multiplier=1, min=2, max=10),
    "retry": retry_if_exception_type((OpenAIRateLimitError, AnthropicRateLimitError, Exception)), # 包含网络连接异常
}

class LLMResponse(BaseModel):
    """
    LLM 统一响应数据结构。
    """
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str


class LLMFactory:
    """
    LLM 接口调度工厂。
    负责根据数据库配置进行模型调用路由与客户端管理。
    """

    def __init__(self):
        """
        初始化调度工厂。
        """
        self.supabase = SupabaseManager()
        self.openai_clients: Dict[str, OpenAI] = {}
        self.openai_async_clients: Dict[str, AsyncOpenAI] = {}
        self.anthropic_client: Any = None
        self.anthropic_async_client: Any = None

    def get_config(self, identifier: str) -> Dict[str, Any]:
        """
        获取智能体配置。实现“Agent 覆盖 > 系统默认”的生产级继承逻辑。
        """
        # 1. 首先获取全局默认配置作为基准
        config = self.get_default_config()

        # 2. 尝试从数据库获取特定 Agent 的配置
        agent_data = self.supabase.get_agent_config(identifier)
        
        # 如果 Agent 存在，执行字段级覆盖
        if agent_data:
            provider = agent_data.get("llm_providers")
            if provider:
                # 如果 Agent 关联了具体的供应商，则覆盖全局供应商信息
                config["provider_type"] = provider.get("type")
                config["api_base"] = provider.get("api_base")
                config["api_token"] = provider.get("api_token")
            
            # 覆盖模型和参数
            if agent_data.get("model"):
                config["model"] = agent_data["model"]
            if agent_data.get("temperature") is not None:
                config["temperature"] = agent_data["temperature"]

        return config

    def get_default_config(self) -> Dict[str, Any]:
        """
        获取系统全局默认 LLM 配置。 (本地优先版)
        """
        from core.prompt_manager import prompt_manager
        
        # 仍然从数据库获取 API Key 等敏感信息，但提示词改用本地
        settings = self.supabase.get_system_settings()
        if not settings:
            raise RuntimeError("CRITICAL ERROR: System settings not found in database for API keys.")

        provider = settings.get("llm_providers")
        if not provider:
            raise RuntimeError("CRITICAL ERROR: Default LLM provider is not configured.")

        config = {
            "provider_type": provider.get("type"),
            "api_base": provider.get("api_base"),
            "api_token": provider.get("api_token"),
            "model": settings.get("default_model"),
            "core_system_prompt": prompt_manager.get_prompt("core_system_prompt"), # 核心修改：使用本地提示词
            "temperature": 0.7
        }

        return config

    def validate_config(self, config: Dict[str, Any]):
        """执行严格的生产级配置校验"""
        required_keys = ["provider_type", "api_token", "model"]
        missing = [k for k in required_keys if not config.get(k)]
        if missing:
            raise RuntimeError(
                f"LLM 配置校验失败！缺失项: {', '.join(missing)}。\n"
                f"系统已尝试从 Agent 专属配置和全局默认配置中获取，但均未找到有效的 API Key。\n"
                f"请前往 Admin 后台的【模型配置】或【智能体设置】中填入供应商的 API Token。"
            )

    def call_llm(self, identifier: str, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """
        执行大语言模型调用。
        """
        config = self.get_config(identifier)
        return self._execute_call(config, messages, **kwargs)

    def call_default_llm(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """
        使用系统默认配置执行大语言模型调用。
        """
        config = self.get_default_config()
        return self._execute_call(config, messages, **kwargs)

    def _execute_call(self, config: Dict, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """
        统一的调用执行入口 (包含前置强校验)。
        """
        self.validate_config(config)
        protocol = config["provider_type"].lower()
        if protocol == "openai":
            return self._call_openai(config, messages, **kwargs)
        elif protocol == "anthropic":
            return self._call_anthropic(config, messages, **kwargs)
        else:
            raise ValueError(f"不支持的供应商协议: {protocol}")

    def call_llm_stream(self, identifier: str, messages: List[Dict[str, str]], **kwargs):
        """
        执行大语言模型流式调用。
        """
        config = self.get_config(identifier)
        return self._execute_stream_call(config, messages, **kwargs)

    def call_default_llm_stream(self, messages: List[Dict[str, str]], **kwargs):
        """
        使用系统默认配置执行大语言模型流式调用。
        """
        config = self.get_default_config()
        return self._execute_stream_call(config, messages, **kwargs)

    def _execute_stream_call(self, config: Dict, messages: List[Dict[str, str]], **kwargs):
        """
        统一的流式调用执行入口。
        """
        protocol = config["provider_type"].lower()
        if protocol == "openai":
            return self._call_openai_stream(config, messages, **kwargs)
        elif protocol == "anthropic":
            return self._call_anthropic_stream(config, messages, **kwargs)
        else:
            raise ValueError(f"不支持的供应商协议: {protocol}")

    def call_llm_stream_async(self, identifier: str, messages: List[Dict[str, str]], **kwargs):
        """
        执行大语言模型异步流式调用。
        """
        config = self.get_config(identifier)
        return self._execute_stream_call_async(config, messages, **kwargs)

    async def _execute_stream_call_async(self, config: Dict, messages: List[Dict[str, str]], **kwargs):
        """
        统一的异步流式调用执行入口 (包含前置强校验)。
        """
        self.validate_config(config)
        protocol = config["provider_type"].lower()
        if protocol == "openai":
            async for chunk in self._call_openai_stream_async(config, messages, **kwargs):
                yield chunk
        elif protocol == "anthropic":
            async for chunk in self._call_anthropic_stream_async(config, messages, **kwargs):
                yield chunk
        else:
            raise ValueError(f"不支持的供应商协议: {protocol}")

    async def _call_openai_stream_async(self, config: Dict, messages: List[Dict], **kwargs):
        """
        通过 OpenAI 协议发起异步流式 API 请求 (具备生产级重试机制)。
        """
        client = self._get_openai_async_client(config["api_base"], config["api_token"])
        model = config["model"]
        
        params = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", config["temperature"]),
            "stream": True,
            **kwargs
        }

        async for attempt in AsyncRetrying(**RETRY_CONFIG):
            with attempt:
                try:
                    stream = await client.chat.completions.create(**params)
                    async for chunk in stream:
                        if chunk.choices and chunk.choices[0].delta.content:
                            yield chunk.choices[0].delta.content
                except (OpenAIRateLimitError, Exception) as e:
                    if attempt.retry_state.attempt_number < 3:
                        print(f"[LLM] OpenAI 调用异常 (重试 {attempt.retry_state.attempt_number}/3): {str(e)[:100]}...")
                    raise e

    async def _call_anthropic_stream_async(self, config: Dict, messages: List[Dict], **kwargs):
        """
        通过 Anthropic 协议发起异步流式 API 请求 (具备生产级重试机制)。
        """
        if not self.anthropic_async_client or self.anthropic_async_client.api_key != config["api_token"]:
            self.anthropic_async_client = AsyncAnthropic(api_key=config["api_token"])
        
        model = config["model"]
        system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_msgs = [m for m in messages if m["role"] != "system"]

        async for attempt in AsyncRetrying(**RETRY_CONFIG):
            with attempt:
                try:
                    async with self.anthropic_async_client.messages.stream(
                        model=model,
                        max_tokens=kwargs.get("max_tokens", 4096),
                        system=system_msg,
                        messages=user_msgs,
                        temperature=kwargs.get("temperature", config["temperature"])
                    ) as stream:
                        async for text in stream.text_stream:
                            yield text
                except Exception as e:
                    if attempt.retry_state.attempt_number < 3:
                        print(f"[LLM] Anthropic 调用异常 (重试 {attempt.retry_state.attempt_number}/3): {str(e)[:100]}...")
                    raise e

    def _get_openai_client(self, api_base: str, api_token: str) -> OpenAI:
        """
        获取缓存的 OpenAI 客户端实例。
        """
        cache_key = f"{api_base}_{api_token}"
        if cache_key not in self.openai_clients:
            self.openai_clients[cache_key] = OpenAI(api_key=api_token, base_url=api_base)
        return self.openai_clients[cache_key]

    def _get_openai_async_client(self, api_base: str, api_token: str) -> AsyncOpenAI:
        """
        获取缓存的 OpenAI 异步客户端实例。
        """
        cache_key = f"{api_base}_{api_token}"
        if cache_key not in self.openai_async_clients:
            self.openai_async_clients[cache_key] = AsyncOpenAI(api_key=api_token, base_url=api_base)
        return self.openai_async_clients[cache_key]

    @retry(**RETRY_CONFIG)
    def _call_openai(self, config: Dict, messages: List[Dict], **kwargs) -> LLMResponse:
        """
        通过 OpenAI 协议发起 API 请求。
        """
        client = self._get_openai_client(config["api_base"], config["api_token"])
        model = config["model"]
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=kwargs.get("temperature", config["temperature"]),
            **kwargs
        )
        return LLMResponse(
            content=response.choices[0].message.content,
            model=model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            finish_reason=response.choices[0].finish_reason
        )

    def _call_openai_stream(self, config: Dict, messages: List[Dict], **kwargs):
        """
        通过 OpenAI 协议发起流式 API 请求。
        """
        client = self._get_openai_client(config["api_base"], config["api_token"])
        model = config["model"]
        
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=kwargs.get("temperature", config["temperature"]),
            stream=True,
            **kwargs
        )
        
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(AnthropicRateLimitError),
        before_sleep=lambda retry_state: print(f"[LLM] Anthropic 并发限制，正在重试 ({retry_state.attempt_number}/3)，等待 {retry_state.next_action.sleep}s...")
    )
    @retry(**RETRY_CONFIG)
    def _call_anthropic(self, config: Dict, messages: List[Dict], **kwargs) -> LLMResponse:
        """
        通过 Anthropic 协议发起 API 请求。
        """
        if not self.anthropic_client or self.anthropic_client.api_key != config["api_token"]:
            self.anthropic_client = Anthropic(api_key=config["api_token"])
        
        model = config["model"]
        system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_msgs = [m for m in messages if m["role"] != "system"]

        response = self.anthropic_client.messages.create(
            model=model,
            max_tokens=kwargs.get("max_tokens", 4096),
            system=system_msg,
            messages=user_msgs,
            temperature=kwargs.get("temperature", config["temperature"])
        )
        
        return LLMResponse(
            content=response.content[0].text,
            model=model,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            },
            finish_reason=response.stop_reason or "stop"
        )

    def _call_anthropic_stream(self, config: Dict, messages: List[Dict], **kwargs):
        """
        通过 Anthropic 协议发起流式 API 请求。
        """
        if not self.anthropic_client or self.anthropic_client.api_key != config["api_token"]:
            self.anthropic_client = Anthropic(api_key=config["api_token"])
        
        model = config["model"]
        system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_msgs = [m for m in messages if m["role"] != "system"]

        with self.anthropic_client.messages.stream(
            model=model,
            max_tokens=kwargs.get("max_tokens", 4096),
            system=system_msg,
            messages=user_msgs,
            temperature=kwargs.get("temperature", config["temperature"])
        ) as stream:
            for text in stream.text_stream:
                yield text