"""
编排执行管线 (Orchestration Pipeline)

职责：驱动全量拓扑清单的物理执行。
支持“断点续传”：自动同步 Session 历史中的已完成节点，仅驱动增量逻辑。
"""

import asyncio
from typing import Dict, Any, List, Optional
from core.schema.orchestration import WorkflowManifest, DispatchItem
from core.session.session import Session
from core.orchestrator.schema import OrchestrationSnapshot, NodeStatus, TaskResult
from core.orchestrator.resolver import DependencyResolver
from core.orchestrator.dispatcher import dispatcher
from core.schema.message import MessageRole

class WorkflowPipeline:
    """
    工作流编排引擎实体。
    """

    def __init__(self, manifest: WorkflowManifest, session: Session, current_dispatches: List[DispatchItem]):
        self.manifest = manifest
        self.session = session
        self.resolver = DependencyResolver(manifest)
        self.snapshot = OrchestrationSnapshot(session_id=session.id)
        
        # 1. 历史复水：从 Session History 中识别已完成的任务
        self._rehydrate_history()
        
        # 2. 注入当前批次的执行参数
        self._execution_payloads: Dict[str, Dict[str, Any]] = {
            item.node_id: item.arguments for item in current_dispatches
        }

    def _rehydrate_history(self):
        """
        [逻辑核心] 状态复水。
        扫描会话历史，将所有已经产生过 TOOL 响应的节点标记为 COMPLETED。
        """
        for msg in self.session.history:
            if msg.role == MessageRole.TOOL and msg.tool_call_id:
                # 如果历史记录中有这个节点的产出，标记为完成
                self.snapshot.node_states[msg.tool_call_id] = NodeStatus.COMPLETED
                self.snapshot.results[msg.tool_call_id] = TaskResult(
                    node_id=msg.tool_call_id,
                    status="success",
                    output=msg.content
                )

    async def execute(self) -> OrchestrationSnapshot:
        """
        驱动编排循环。
        """
        iteration = 0
        while True:
            iteration += 1
            # 探测满足前序依赖且未完成的节点
            ready_node_ids = self.resolver.get_ready_nodes(self.snapshot)
            
            # 过滤掉虽然 ready 但本次没有 dispatch 载荷的节点 (它们可能在等待模型下一轮填充)
            launchable_ids = [nid for nid in ready_node_ids if nid in self._execution_payloads]

            print(f"\033[36m[Pipeline Trace] Iteration {iteration}: 就绪节点={ready_node_ids}, 本次可启动节点={launchable_ids}\033[0m")

            if not launchable_ids:
                # 检查是否还有正在运行的节点
                active_nodes = [nid for nid, status in self.snapshot.node_states.items() if status == NodeStatus.RUNNING]
                if not active_nodes:
                    print(f"\033[36m[Pipeline Trace] 无可启动节点且无运行中节点，流水线退出。\033[0m")
                    break
                await asyncio.sleep(0.05)
                continue

            tasks = []
            for node_id in launchable_ids:
                print(f"\033[32m[Pipeline Trace] 🚀 正在启动节点: {node_id}\033[0m")
                self.snapshot.node_states[node_id] = NodeStatus.RUNNING
                node_data = self.resolver.nodes[node_id]
                tasks.append(self._run_node(node_data))

            await asyncio.gather(*tasks)

        return self.snapshot

    async def _run_node(self, node: Any):
        """执行单个节点并同步状态。"""
        arguments = self._execution_payloads.get(node.id, {})
        
        # 显式物理调用日志
        print(f"\033[1;33m[Dispatcher] 正在调用能力: {node.capability} (Node: {node.id})\033[0m")
        
        # 物理派发
        result = await dispatcher.dispatch(
            node_id=node.id,
            capability=node.capability,
            arguments=arguments,
            session=self.session
        )
        
        # 实时记录事实 (Phase 2 Commit)
        if result.status == "success":
            print(f"\033[32m[Pipeline Trace] ✅ 节点完成: {node.id}\033[0m")
            self.snapshot.mark_completed(node.id, result)
        else:
            print(f"\033[31m[Pipeline Trace] ❌ 节点失败: {node.id} | 原因: {result.error}\033[0m")
            self.snapshot.mark_failed(node.id, result.error or "Unknown")
