import os
import yaml
from typing import Dict, Any, List, Optional
from openai import OpenAI
from anthropic import Anthropic
from pydantic import BaseModel
from core.supabase_manager import SupabaseManager

class LLMResponse(BaseModel):
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str

class LLMFactory:
    """
    多供应商 LLM 工厂：支持从 Supabase 动态加载层级化配置。
    优先级：Agent 覆盖 > Provider 默认 > 环境变量
    """
    
    def __init__(self, config_path: str = "config/agents.yaml"):
        self.config_path = config_path
        self.local_configs = self._load_local_config()
        self.supabase = SupabaseManager()
        self.openai_clients: Dict[str, OpenAI] = {}
        self.anthropic_client: Optional[Anthropic] = None

    def _load_local_config(self) -> Dict[str, Any]:
        if not os.path.exists(self.config_path):
            return {}
        with open(self.config_path, "r", encoding="utf-8") as f:
            try:
                return yaml.safe_load(f).get("agents", {})
            except:
                return {}

    def _get_merged_config(self, agent_type: str) -> Dict[str, Any]:
        """合并 Agent 专属配置与供应商全局配置"""
        agent_id = f"{agent_type}_agent"
        db_agent = self.supabase.get_agent_config(agent_id)
        
        # 基础骨架（从本地 fallback 开始）
        final_config = self.local_configs.get(agent_type, self.local_configs.get("default", {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.7
        }))

        if db_agent:
            provider_name = db_agent.get("provider", "openai")
            db_provider = self.supabase.get_provider_config(provider_name)
            
            # 1. 应用供应商默认配置
            if db_provider:
                final_config["provider"] = provider_name
                final_config["api_base"] = db_provider.get("api_base")
                final_config["api_token"] = db_provider.get("api_token")
            
            # 2. 应用 Agent 级别覆盖（最高优先级）
            if db_agent.get("model"): final_config["model"] = db_agent["model"]
            if db_agent.get("temperature") is not None: final_config["temperature"] = db_agent["temperature"]
            if db_agent.get("system_prompt"): final_config["system_prompt"] = db_agent["system_prompt"]
            if db_agent.get("api_base"): final_config["api_base"] = db_agent["api_base"]
            if db_agent.get("api_token"): final_config["api_token"] = db_agent["api_token"]

        return final_config

    def _get_openai_client(self, api_base: str, api_token: str) -> OpenAI:
        cache_key = f"{api_base}_{api_token}"
        if cache_key not in self.openai_clients:
            self.openai_clients[cache_key] = OpenAI(api_key=api_token, base_url=api_base)
        return self.openai_clients[cache_key]

    def _get_anthropic_client(self, api_token: str) -> Anthropic:
        if not self.anthropic_client or self.anthropic_client.api_key != api_token:
            self.anthropic_client = Anthropic(api_key=api_token)
        return self.anthropic_client

    def call_llm(self, agent_type: str, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """
        统一调用接口（支持多级配置合并与多供应商切换）
        """
        config = self._get_merged_config(agent_type)
        provider = config.get("provider", "openai").lower()
        model = config.get("model", "gpt-4o-mini")
        
        # 获取最终的 Auth 凭证
        api_token = config.get("api_token") or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        api_base = config.get("api_base")

        # Mock 模式检测
        if not api_token:
            return self._generate_mock_response(agent_type, messages)

        if provider in ["openai", "deepseek"]:
            # 默认补全 OpenAI 地址
            base_url = api_base or "https://api.openai.com/v1"
            return self._call_openai(config, messages, base_url, api_token, **kwargs)
        elif provider == "anthropic":
            return self._call_anthropic(config, messages, api_token, **kwargs)
        else:
            raise ValueError(f"不支持的供应商: {provider}")

    def _call_openai(self, config: Dict, messages: List[Dict], api_base: str, api_token: str, **kwargs) -> LLMResponse:
        client = self._get_openai_client(api_base, api_token)
        response = client.chat.completions.create(
            model=config.get("model"),
            messages=messages,
            temperature=kwargs.get("temperature", config.get("temperature", 0.7)),
            **kwargs
        )
        return LLMResponse(
            content=response.choices[0].message.content,
            model=config.get("model"),
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            finish_reason=response.choices[0].finish_reason
        )

    def _call_anthropic(self, config: Dict, messages: List[Dict], api_token: str, **kwargs) -> LLMResponse:
        client = self._get_anthropic_client(api_token)
        
        system_msg = ""
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                user_messages.append(msg)

        response = client.messages.create(
            model=config.get("model"),
            max_tokens=kwargs.get("max_tokens", 4096),
            system=system_msg,
            messages=user_messages,
            temperature=kwargs.get("temperature", config.get("temperature", 0.7))
        )
        
        return LLMResponse(
            content=response.content[0].text,
            model=config.get("model"),
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            },
            finish_reason=response.stop_reason or "stop"
        )

    def _generate_mock_response(self, agent_type: str, messages: List[Dict[str, str]]) -> LLMResponse:
        last_msg = messages[-1]["content"]
        content = f"[Mock {agent_type.upper()}] 因为未检测到 API Token，已自动进入 Mock 模式。指令: '{last_msg[:30]}...'"
        return LLMResponse(
            content=content,
            model="mock-model",
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            finish_reason="stop"
        )
