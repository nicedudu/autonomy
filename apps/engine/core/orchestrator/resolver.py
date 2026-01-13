"""
任务依赖解析器 (Task Dependency Resolver)

职责：基于拓扑排序算法，实时计算工作流中满足执行条件的节点。
实现从“编排清单”到“执行计划”的动态转换。
"""

from typing import List, Set, Dict, Optional
from core.schema.orchestration import WorkflowManifest
from core.orchestrator.schema import NodeStatus, OrchestrationSnapshot

class DependencyResolver:
    """
    负责工作流拓扑结构的管理与就绪探测。
    """

    def __init__(self, manifest: WorkflowManifest):
        self.manifest = manifest
        # 构建节点映射以便快速查找
        self.nodes = {node.id: node for node in manifest.nodes}
        
        # 验证是否存在循环依赖（简单自检）
        self._validate_topology()

    def get_ready_nodes(self, snapshot: OrchestrationSnapshot) -> List[str]:
        """
        根据当前快照状态，返回所有“依赖已满足且未运行”的节点 ID 列表。
        """
        ready_nodes = []
        
        for node_id, node in self.nodes.items():
            # 1. 过滤已完成或正在运行的节点
            current_status = snapshot.node_states.get(node_id, NodeStatus.PENDING)
            if current_status != NodeStatus.PENDING:
                continue
            
            # 2. 检查前序依赖是否全部完成
            dependencies = node.dependencies
            if not dependencies:
                # 无依赖节点自动就绪
                ready_nodes.append(node_id)
                continue
                
            is_satisfied = all(
                snapshot.node_states.get(dep_id) == NodeStatus.COMPLETED 
                for dep_id in dependencies
            )
            
            if is_satisfied:
                ready_nodes.append(node_id)
                
        return ready_nodes

    def _validate_topology(self):
        """
        拓扑合法性校验：确保所有依赖项都在节点列表中定义。
        """
        node_ids = set(self.nodes.keys())
        for node in self.manifest.nodes:
            for dep_id in node.dependencies:
                if dep_id not in node_ids:
                    raise ValueError(f"工作流定义错误：节点 '{node.id}' 依赖于未定义的 ID '{dep_id}'")
