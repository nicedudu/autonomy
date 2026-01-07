"""
执行单元工厂 (Execution Unit Factory)

本模块负责分布式执行节点的生命周期管理。
通过集成配置解析器实现按需路由，支持基于执行蓝图的动态实例化与资源装配。
"""

from typing import Any, Dict, List, Optional
from core.agent.runtime import AgentRuntime
from core.schema.collaboration import ExecutionBlueprint
from core.registry.internal import get_agent_definition, AgentDefinition
from core.llm.resolver import config_resolver
from core.utils.logging import logger

class ExecutionUnitFactory:
    """
    智能体执行单元生产工厂。
    
    统一协调静态专家节点与动态临时节点的创建流程，确立全链路配置驱动机制。
    """

    @staticmethod
    def create_runtime(
        agent_id: str,
        session_id: str,
        blueprint: Optional[ExecutionBlueprint] = None
    ) -> AgentRuntime:
        """
        创建标准执行运行时。
        
        Args:
            agent_id: 智能体标识符。若为 'dynamic' 则触发动态实例化。
            session_id: 关联会话唯一标识。
            blueprint: 任务执行蓝图规格。
            
        Returns:
            AgentRuntime: 初始化完成的执行内核。
        """
        # 1. 策略路由：检索静态定义或合成动态定义
        definition = get_agent_definition(agent_id)
        
        if not definition:
            if agent_id == "dynamic" and blueprint:
                definition = AgentDefinition(
                    agent_id="dynamic_worker",
                    name="临时执行节点",
                    role="Dynamic Task Executor",
                    capabilities=blueprint.resource.capability_mask,
                    template_name="kernel"
                )
            else:
                raise ValueError(f"执行单元定义不存在: '{agent_id}'")

        # 2. 模型配置解析 (SSOT)
        # 彻底移除硬编码占位符，强制从 Resolver 获取真实配置
        config = config_resolver.resolve(agent_id)
        
        # 3. 审计日志：输出脱敏后的配置指纹
        safe_key = f"{config['api_key'][:6]}...{config['api_key'][-4:]}" if config['api_key'] else "None"
        logger.debug(
            f"装配节点算力: model={config['model']}, provider={config['provider_type']}, "
            f"endpoint={config['base_url']}, key={safe_key}", 
            agent_id
        )

        # 4. 装配中间件并初始化内核
        from core.agent.factory_utils import get_default_middlewares
        
        return AgentRuntime(
            agent_id=agent_id,
            provider_type=config['provider_type'],
            model=config['model'],
            api_key=config['api_key'],
            base_url=config['base_url'],
            middlewares=get_default_middlewares(),
            max_steps=blueprint.max_steps if blueprint else 15
        )

    @staticmethod
    def create_from_blueprint(blueprint: ExecutionBlueprint, session_id: str) -> AgentRuntime:
        """根据执行蓝图契约 JIT 生产执行单元。"""
        return ExecutionUnitFactory.create_runtime(
            agent_id=blueprint.target_service,
            session_id=session_id,
            blueprint=blueprint
        )