"""
智能体提示词架构师 (Prompt Architect)

职责：实现智能体规格（AgentProfile）的动态合成。
遵循标准算力路由协议，支持通过 Admin 端（Supabase）独立配置其推理引擎。
"""

import json
from typing import List, Optional
from core.agent.profile import AgentProfile
from core.llm.manager import llm_manager
from core.llm.schema import LLMMessage, LLMRole, InferenceConfig
from core.llm.resolver import config_resolver
from core.prompt.compiler import prompt_compiler
from core.tools.registry import tool_registry
from core.agent.registry import agent_registry

class PromptArchitect:
    """
    智能体动态合成器。
    """

    def __init__(self):
        # 核心修正：使用专属标识符解析算力配置
        # 逻辑：优先查找 agents 表中 identifier='prompt_architect' 的配置，若无则回退至系统默认
        self.config = config_resolver.resolve("prompt_architect")
        self.client = llm_manager.create_client(self.config)

    async def synthesize(self, requirement_spec: str) -> AgentProfile:
        """
        根据需求规格动态合成一个新的 AgentProfile。
        """
        # 1. 准备全域能力快照
        full_capabilities = {
            "tools": list(tool_registry._tools.keys()),
            "agents": agent_registry.get_agents()
        }

        # 2. 编译架构师指令
        system_prompt = prompt_compiler.env.get_template("architect.j2").render(
            full_capability_list=json.dumps(full_capabilities, ensure_ascii=False),
            requirement_spec=requirement_spec
        )

        # 3. 发起合成推理
        # 采用极低随机性以确保 JSON 结构的稳定性
        response = await self.client.generate(
            messages=[LLMMessage(role=LLMRole.USER, content=f"请为我设计一个智能体规格，需求如下：{requirement_spec}")],
            system=system_prompt,
            config=InferenceConfig(temperature=0.1, max_tokens=2048)
        )

        # 4. 契约化解析
        try:
            from core.utils.json_utils import extract_json
            data = extract_json(response.content)
            
            # 强制补全模板标识
            if "template_id" not in data:
                data["template_id"] = "assistant"
                
            return AgentProfile.model_validate(data)
        except Exception as e:
            raise RuntimeError(f"智能体合成失败：无法解析模型产出的 Profile 契约。详情: {e}")

# 导出架构师单例
prompt_architect = PromptArchitect()
