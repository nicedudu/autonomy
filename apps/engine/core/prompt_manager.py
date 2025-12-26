import os
import yaml
from jinja2 import Template, Environment
from typing import Dict, Any, Optional
from core.supabase_manager import SupabaseManager

class PromptManager:
    """
    Prompt 资产管理器
    负责加载 Prompt 模板并利用上下文数据进行渲染。
    支持从 Supabase 动态加载实现云端维护。
    """
    
    def __init__(self, prompt_path: str = "prompts/library.yaml"):
        self.prompt_path = prompt_path
        self.local_prompts = self._load_local_prompts()
        self.supabase = SupabaseManager()
        self.env = Environment()

    def _load_local_prompts(self) -> Dict[str, Any]:
        """加载本地 Prompt 配置文件"""
        if not os.path.exists(self.prompt_path):
            return {}
        with open(self.prompt_path, "r", encoding="utf-8") as f:
            try:
                return yaml.safe_load(f) or {}
            except yaml.YAMLError:
                return {}

    def get_system_prompt(self, agent_type: str) -> Optional[str]:
        """
        获取 Agent 的 System Prompt
        :param agent_type: agent 类型 (e.g., 'cpo', 'scm')
        """
        # 1. 尝试从 Supabase 获取
        slug = f"{agent_type}_system"
        prompt = self.supabase.get_prompt_template(slug)
        if prompt:
            return prompt
            
        # 2. 回退到本地
        agent_config = self.local_prompts.get("agents", {}).get(agent_type, {})
        return agent_config.get("system")

    def render_prompt(self, agent_type: str, prompt_key: str, **kwargs) -> str:
        """
        获取并渲染特定的 Prompt 模板（云端优先策略）
        :param agent_type: agent 类型 (e.g., 'cpo', 'scm')
        :param prompt_key: prompt 的键名 (e.g., 'strategic_insight')
        :param kwargs: 用于渲染模板的变量
        """
        slug = f"{agent_type}_{prompt_key}"
        
        # 1. 尝试从 Supabase 获取
        template_str = self.supabase.get_prompt_template(slug)
        
        # 2. 回退到本地
        if not template_str:
            agent_config = self.local_prompts.get("agents", {}).get(agent_type, {})
            template_str = agent_config.get(prompt_key)
        
        if not template_str:
            return f"Error: Prompt template {slug} not found."
            
        try:
            template = self.env.from_string(template_str)
            return template.render(**kwargs)
        except Exception as e:
            print(f"[PromptManager] Error rendering prompt: {e}")
            return template_str
            
    def reload(self):
        """重新加载本地 Prompt 文件"""
        self.local_prompts = self._load_local_prompts()