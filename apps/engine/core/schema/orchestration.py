"""
工作流编排数据契约 (Orchestration Schema Specification)

本模块定义了任务编排层的标准化数据模型。
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

class ExecutionMode(str, Enum):
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"

class DynamicSynthesisConfig(BaseModel):
    enabled: bool = False
    requirement_spec: str = Field(..., description="动态合成规格需求")

class TaskNode(BaseModel):
    """
    任务节点。
    """
    id: str = Field(..., description="节点 ID")
    task_name: str = Field(..., description="任务名称")
    capability: str = Field(..., description="能力标识符")
    
    description: Optional[str] = None 
    dependencies: List[str] = Field(default_factory=list)
    execution_mode: ExecutionMode = ExecutionMode.PARALLEL
    dynamic_synthesis: Optional[DynamicSynthesisConfig] = None

class WorkflowMetadata(BaseModel):
    total_tasks: Optional[int] = 0
    concurrency_limit: Optional[int] = 5

class WorkflowManifest(BaseModel):
    """工作流清单"""
    workflow_metadata: Optional[WorkflowMetadata] = Field(default_factory=WorkflowMetadata)
    nodes: List[TaskNode]
    summary: Optional[str] = None

class DispatchItem(BaseModel):
    node_id: str = Field(..., description="节点 ID")
    arguments: Dict[str, Any] = Field(default_factory=dict)