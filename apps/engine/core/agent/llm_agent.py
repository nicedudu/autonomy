from typing import List, Dict, Any, Optional
from core.agent.base import BaseAgent
from core.agent.state import AgentState, AgentMessage, MessageRole
from core.llm.service import LLMService
from core.schema.models import AgentManifest, LLMConfig

class LLMAgent(BaseAgent):
    """
    基于 LLM 的智能体实现。
    负责消息格式化、System Prompt 编译以及调用 LLM 服务。
    """

    def __init__(
        self, 
        manifest: AgentManifest, 
        llm_service: Optional[LLMService] = None,
        llm_config: Optional[LLMConfig] = None
    ):
        super().__init__(manifest)
        self.llm_service = llm_service or LLMService()
        self.llm_config = llm_config or manifest.llm_config

    def get_system_prompt(self, state: AgentState) -> str:
        """
        构建系统提示词。
        指令来源于核心库中的 AgentDefinition (INTERNAL_AGENTS)。
        """
        from core.registry.internal import get_internal_agent
        from core.prompt.compiler import prompt_compiler
        
        # 1. 获取内置核心指令
        definition = get_internal_agent(self.agent_id)
        if not definition:
            return "You are a helpful AI assistant."

        try:
            return prompt_compiler.compile_agent_prompt(definition, state)
        except Exception:
            # Fallback if compilation fails
            return "You are a helpful AI assistant."

    async def think(self, state: AgentState, system_prompt_override: Optional[str] = None) -> AgentMessage:
        """
        调用 LLM 进行一轮推理。
        """
        # 1. 准备消息列表
        sys_prompt = system_prompt_override or self.get_system_prompt(state)
        messages = [{"role": MessageRole.SYSTEM, "content": sys_prompt}]
        
        # 转换历史消息为 LLM 格式
        for msg in state.history:
            messages.append({"role": msg.role, "content": msg.content})

        # 2. 调用 LLM Service (流式聚合为完整响应)
        full_content = ""
        # 注意：此处为聚合调用，流式输出由 Runtime 层的 yield 处理 (本层暂不直接 yield)
        async for chunk in self.llm_service.stream(self.llm_config, messages):
            full_content += chunk

        # 3. 封装为 AgentMessage 返回
        return AgentMessage(
            role=MessageRole.ASSISTANT,
            content=full_content
        )
