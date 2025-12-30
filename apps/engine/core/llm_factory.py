import os
import asyncio
from typing import Any, Dict, List

from anthropic import Anthropic, AsyncAnthropic, RateLimitError as AnthropicRateLimitError
from core.supabase_manager import SupabaseManager
from openai import OpenAI, AsyncOpenAI, RateLimitError as OpenAIRateLimitError
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


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
        获取指定智能体的完整配置信息。
        """
        agent_data = self.supabase.get_agent_config(identifier)
        if not agent_data:
            raise RuntimeError(f"未找到智能体配置: {identifier}")

        provider = agent_data.get("llm_providers")
        if not provider:
            raise RuntimeError(f"智能体未关联供应商: {identifier}")

        config = {
            "provider_type": provider.get("type"),
            "api_base": provider.get("api_base"),
            "api_token": provider.get("api_token"),
            "model": agent_data.get("model"),
            "temperature": agent_data.get("temperature", 0.7),
            "system_prompt": agent_data.get("system_prompt"),
            "user_prompt": agent_data.get("user_prompt")
        }

        # 校验必填配置项
        required_keys = ["provider_type", "api_token", "model", "system_prompt", "user_prompt"]
        missing = [k for k in required_keys if not config.get(k)]
        if missing:
            raise RuntimeError(f"智能体 '{identifier}' 配置项缺失: {', '.join(missing)}")

        return config

    def get_default_config(self) -> Dict[str, Any]:
        """
        获取系统默认 LLM 配置。
        """
        settings = self.supabase.get_system_settings()
        if not settings:
            raise RuntimeError("系统全局 LLM 配置缺失: 请在管理后台进行配置。")

        provider = settings.get("llm_providers")
        if not provider:
            raise RuntimeError("系统默认 LLM 供应商未关联或已失效。")

        config = {
            "provider_type": provider.get("type"),
            "api_base": provider.get("api_base"),
            "api_token": provider.get("api_token"),
            "model": settings.get("default_model"),
            "temperature": 0.7
        }

        # 校验必填配置项
        required_keys = ["provider_type", "api_token", "model"]
        missing = [k for k in required_keys if not config.get(k)]
        if missing:
            raise RuntimeError(f"系统默认配置项缺失: {', '.join(missing)}")

        return config

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
        统一的调用执行入口。
        """
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
        统一的异步流式调用执行入口。
        """
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
        通过 OpenAI 协议发起异步流式 API 请求。
        """
        client = self._get_openai_async_client(config["api_base"], config["api_token"])
        model = config["model"]
        
        # 确保基础配置
        params = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", config["temperature"]),
            "stream": True,
            **kwargs
        }

        stream = await client.chat.completions.create(**params)
        
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                yield content

    async def _call_anthropic_stream_async(self, config: Dict, messages: List[Dict], **kwargs):
        """
        通过 Anthropic 协议发起异步流式 API 请求。
        """
        if not self.anthropic_async_client or self.anthropic_async_client.api_key != config["api_token"]:
            self.anthropic_async_client = AsyncAnthropic(api_key=config["api_token"])
        
        model = config["model"]
        system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_msgs = [m for m in messages if m["role"] != "system"]

        async with self.anthropic_async_client.messages.stream(
            model=model,
            max_tokens=kwargs.get("max_tokens", 4096),
            system=system_msg,
            messages=user_msgs,
            temperature=kwargs.get("temperature", config["temperature"])
        ) as stream:
            async for text in stream.text_stream:
                yield text

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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(OpenAIRateLimitError),
        before_sleep=lambda retry_state: print(f"[LLM] OpenAI 并发限制，正在重试 ({retry_state.attempt_number}/3)，等待 {retry_state.next_action.sleep}s...")
    )
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