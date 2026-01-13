"""
编排引擎数据契约 (Orchestrator Schema Specification)

本模块定义了任务在编排调度过程中的中间状态与执行快照。
通过 NodeStatus 维护生命周期，通过 TaskResult 承载任务产出，实现执行流的数据闭环。
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class NodeStatus(str, Enum):
    """任务节点生命周期状态"""
    PENDING = "pending"     # 等待前序依赖完成
    READY = "ready"         # 依赖已就绪，等待分派
    RUNNING = "running"     # 正在物理执行
    COMPLETED = "completed" # 执行成功
    FAILED = "failed"       # 执行异常
    SKIPPED = "skipped"     # 因前序失败而跳过

class TaskResult(BaseModel):
    """
    单个任务节点的执行产物。
    """
    node_id: str
    status: str  # success | error
    output: Any = None
    error: Optional[str] = None
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration: float = 0.0 # 耗时秒数

class OrchestrationSnapshot(BaseModel):
    """
    全局编排任务的运行时快照。
    用于记录任务依赖图的实时执行状态。
    """
    session_id: str
    node_states: Dict[str, NodeStatus] = Field(default_factory=dict)
    results: Dict[str, TaskResult] = Field(default_factory=dict)
    
    def mark_completed(self, node_id: str, result: TaskResult):
        """记录完成状态并同步结果"""
        self.node_states[node_id] = NodeStatus.COMPLETED
        self.results[node_id] = result

    def mark_failed(self, node_id: str, error: str):
        """记录失败状态"""
        self.node_states[node_id] = NodeStatus.FAILED
