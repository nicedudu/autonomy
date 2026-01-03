import os
import yaml
from typing import Any, Dict, Optional

class PromptManager:
    """
    Prompt resource management service.
    Handles loading, caching, and variable interpolation from the local library.
    """
    _instance = None
    _library: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PromptManager, cls).__new__(cls)
            cls._instance._load_library()
        return cls._instance

    def _load_library(self):
        """Loads prompt definitions from the standard library path."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        library_path = os.path.join(os.path.dirname(current_dir), "prompts", "library.yaml")
        
        if not os.path.exists(library_path):
            return

        try:
            with open(library_path, "r", encoding="utf-8") as f:
                self._library = yaml.safe_load(f)
        except Exception as e:
            print(f"[PromptManager] Initialization error: {e}")

    def get_prompt(self, path: str, default: str = "") -> str:
        """Retrieves a prompt string by dot-notation path."""
        keys = path.split(".")
        data = self._library
        for k in keys:
            if isinstance(data, dict) and k in data:
                data = data[k]
            else:
                return default
        return str(data) if data else default

    def render(self, path: str, variables: Dict[str, Any], default: str = "") -> str:
        """Retrieves and interpolates a prompt template with provided variables."""
        template = self.get_prompt(path, default)
        for k, v in variables.items():
            template = template.replace(f"{{{{{k}}}}}", str(v))
        return template

# 全局单例
prompt_manager = PromptManager()
