import os
import yaml
from typing import Any, Dict, Optional

class PromptManager:
    """
    提示词资源管理服务。
    负责从本地 Prompt 库加载配置、执行缓存管理以及变量渲染。
    """
    _instance = None
    _library: Dict[str, Any] = {}

    def __new__(cls):
        """单例模式实现，确保全局共用一套提示词缓存。"""
        if cls._instance is None:
            cls._instance = super(PromptManager, cls).__new__(cls)
            cls._instance._load_library()
        return cls._instance

    def _load_library(self):
        """从标准的库路径加载提示词定义文件 (library.yaml)。"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        library_path = os.path.join(os.path.dirname(current_dir), "prompts", "library.yaml")
        
        if not os.path.exists(library_path):
            return

        try:
            with open(library_path, "r", encoding="utf-8") as f:
                self._library = yaml.safe_load(f)
        except Exception as e:
            print(f"[PromptManager] 初始化失败: {e}")

    def get_prompt(self, path: str, default: str = "") -> str:
        """
        通过点分隔路径（如 'tools.researcher.expansion'）检索提示词字符串。
        """
        keys = path.split(".")
        data = self._library
        for k in keys:
            if isinstance(data, dict) and k in data:
                data = data[k]
            else:
                return default
        return str(data) if data else default

    def render(self, path: str, variables: Dict[str, Any], default: str = "") -> str:
        """检索并使用提供的变量渲染提示词模板。"""
        template = self.get_prompt(path, default)
        for k, v in variables.items():
            template = template.replace(f"{{{{{k}}}}}", str(v))
        return template

# 全局提示词管理单例
prompt_manager = PromptManager()