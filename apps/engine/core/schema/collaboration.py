from enum import Enum
from typing import Any, Dict, List
from pydantic import BaseModel, Field

class TaskSpec(BaseModel):
    """子任务逻辑规格模型。"""
    instruction: str
    sop_steps: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)

class ResourceSpec(BaseModel):
    """资源与权限访问规格模型。"""
    artifact_refs: List[str] = Field(default_factory=list)
    capability_mask: List[str] = Field(default_factory=list)

class OutputSpec(BaseModel):
    """交付物规格模型。"""
    expected_format: str = "JSON"
    schema_definition: Dict[str, Any] = Field(default_factory=dict)

class ExecutionMode(str, Enum):
    """执行调度模式。"""
    SYNC = "sync"
    PARALLEL = "parallel"
    BACKGROUND = "async"

class ExecutionBlueprint(BaseModel):
    """执行蓝图契约。
    
    定义分布式任务在执行节点运行所需的完整规格。
    """
    blueprint_id: str
    target_service: str
    mode: ExecutionMode = ExecutionMode.SYNC
    task: TaskSpec
    resource: ResourceSpec
    output: OutputSpec
    max_steps: int = 5
    timeout: int = 60
