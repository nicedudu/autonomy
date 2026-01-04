import os
import asyncio
import json
from typing import Any, Dict, List, Optional

from anthropic import Anthropic, AsyncAnthropic
from core.supabase_manager import SupabaseManager
from openai import OpenAI, AsyncOpenAI, APIStatusError, BadRequestError
from pydantic import BaseModel, Field
from core.registry.manager import discovery_service

class LLMResponse(BaseModel):
    """统一的响应封装结构。"""
    content: str
    model: str
    usage: Any = Field(default_factory=dict) # 放宽类型以兼容所有供应商
    finish_reason: str

class LLMFactory:
    """
    大模型分发工厂 (生产级)。
    职责：
    1. 凭证管理：从 DB 加载 API Key 和 Base URL。
    2. 配置编排：合并系统默认、Agent 清单及运行时参数。
    3. 标准化执行：通过 OpenAI/Anthropic 标准 SDK 进行可靠调用。
    """

    def __init__(self):
        self.supabase = SupabaseManager()
        self._async_clients: Dict[str, AsyncOpenAI] = {}
        self._sync_clients: Dict[str, OpenAI] = {}

    def _get_base_credentials(self) -> Dict[str, Any]:
        """获取系统全局默认的供应商凭证和基础配置。"""
        settings = self.supabase.get_system_settings()
        provider = settings.get("llm_providers") or {}
        
        return {
            "api_key": provider.get("api_token"),
            "base_url": provider.get("api_base"),
            "provider_type": (provider.get("type") or "openai").lower(),
            "model": settings.get("default_model"),
            "temperature": 0.7
        }

    def _resolve_config(self, agent_id: Optional[str]) -> Dict[str, Any]:
        """
        核心配置解析逻辑。
        实现：系统默认 -> 数据库 Agent 记录 -> 本地 YAML 清单 的层级覆盖。
        """
        # 1. 加载基准配置
        config = self._get_base_credentials()
        
        if not agent_id or agent_id == "system_default":
            return config

        # 2. 合并数据库中的 Agent 配置（主要是关联的供应商凭证）
        agent_db = self.supabase.get_agent_config(agent_id)
        if agent_db:
            db_provider = agent_db.get("llm_providers") or {}
            if db_provider:
                config["api_key"] = db_provider.get("api_token") or config["api_key"]
                config["base_url"] = db_provider.get("api_base") or config["base_url"]
                config["provider_type"] = db_provider.get("type") or config["provider_type"]
            
            if agent_db.get("model"):
                config["model"] = agent_db["model"]
            if agent_db.get("temperature") is not None:
                config["temperature"] = agent_db["temperature"]

        # 3. 合并本地 Manifest 覆盖（优先级最高，由开发者直接控制行为）
        local_manifest = discovery_service.agents.get(agent_id)
        if local_manifest and local_manifest.model:
            config["model"] = local_manifest.model

        return config

    def _get_async_client(self, config: Dict) -> AsyncOpenAI:
        """获取并缓存异步客户端实例。"""
        key = f"{config['base_url']}_{config['api_key']}"
        if key not in self._async_clients:
            self._async_clients[key] = AsyncOpenAI(api_key=config['api_key'], base_url=config['base_url'])
        return self._async_clients[key]

    async def call_llm_stream_async(self, agent_id: str, messages: List[Dict[str, str]], **kwargs):
        """
        标准化异步流式调用 (带自动重试)。
        """
        config = self._resolve_config(agent_id)
        client = self._get_async_client(config)
        
        model = kwargs.pop("model", config["model"])
        temperature = kwargs.pop("temperature", config["temperature"])
        
        print(f"\n[LLM Request] Agent: {agent_id} | Model: {model} | Temp: {temperature}")
        
        max_retries = 3
        retry_delay = 2.0
        
        for attempt in range(max_retries + 1):
            try:
                stream = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    stream=True,
                    **kwargs
                )
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                return # 成功执行则退出
                
            except APIStatusError as e:
                if e.status_code == 429: # Rate Limit
                    if attempt < max_retries:
                        wait_time = retry_delay * (2 ** attempt)
                        print(f"\n[LLM Warning] 429 限流，将在 {wait_time}s 后重试 (第 {attempt+1}/{max_retries} 次)...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        print(f"\n[LLM Error] 重试耗尽: {str(e)}")
                        raise e
                else:
                    print(f"\n[LLM Error] API 错误: {str(e)}")
                    raise e
            except Exception as e:
                print(f"\n[LLM Error] 未知异常: {str(e)}")
                raise e

    def call_default_llm(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """
        系统级同步调用逻辑 (带自动重试)。
        """
        config = self._resolve_config("system_default")
        
        # 获取同步客户端
        key = f"{config['base_url']}_{config['api_key']}"
        if key not in self._sync_clients:
            self._sync_clients[key] = OpenAI(api_key=config['api_key'], base_url=config['base_url'])
        client = self._sync_clients[key]

        model = kwargs.pop("model", config["model"])
        temperature = kwargs.pop("temperature", config["temperature"])

        max_retries = 3
        retry_delay = 2.0
        import time

        for attempt in range(max_retries + 1):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    stream=False,
                    **kwargs
                )
                
                usage_raw = response.usage.model_dump() if hasattr(response.usage, 'model_dump') else {}
                
                return LLMResponse(
                    content=response.choices[0].message.content,
                    model=model,
                    usage=usage_raw,
                    finish_reason=response.choices[0].finish_reason
                )
            except APIStatusError as e:
                if e.status_code == 429:
                    if attempt < max_retries:
                        wait_time = retry_delay * (2 ** attempt)
                        print(f"\n[LLM Warning] 系统调用 429 限流，等待 {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"\n[LLM Error] 系统调用重试耗尽: {str(e)}")
                        raise e
                else:
                    print(f"\n[LLM Error] 系统调用失败: {str(e)}")
                    raise e
            except Exception as e:
                print(f"\n[LLM Error] 系统调用异常: {str(e)}")
                raise e