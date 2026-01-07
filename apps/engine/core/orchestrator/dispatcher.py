import asyncio
import json
from typing import Any, AsyncGenerator, Dict, List, Optional
from core.protocol.schema import ProtocolCall
from core.agent.memory import memory_gateway
from core.orchestrator.aggregator import ResultAggregator
from core.communication_bus import bus
from core.schema.collaboration import ExecutionBlueprint, TaskSpec, ResourceSpec, OutputSpec

class Dispatcher:
    """任务编排调度引擎。
    
    支持并发分发与实时事件冒泡，实现分布式执行链的透明化调度。
    """

    def __init__(self):
        self.bus = bus

    async def execute_task(
        self,
        agent_id: str,
        instruction: str,
        session_id: str,
        blueprint: Optional[ExecutionBlueprint] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """驱动任务节点的原子化生命周期并透传流式事件。"""
        from core.agent.factory import ExecutionUnitFactory
        
        runtime = ExecutionUnitFactory.create_runtime(
            agent_id=agent_id, 
            session_id=session_id,
            blueprint=blueprint
        )
        
        async for event in runtime.run(
            input_text=instruction,
            blueprint=blueprint,
            session_id=session_id
        ):
            yield event

    async def dispatch_calls(
        self,
        calls: List[ProtocolCall],
        session_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        并发分发子任务并实时冒泡执行进度。
        
        采用生产级异步队列机制，汇聚多个并发执行单元的事件流。
        
        Yields:
            Dict: 子任务的实时执行事件。
            Final Event: 包含聚合结果的特殊 observation 事件。
        """
        if not calls:
            yield {"type": "observation", "content": "{}"}
            return

        queue = asyncio.Queue()
        pending_tasks = len(calls)

        async def _run_and_collect(call_spec: ProtocolCall):
            nonlocal pending_tasks
            # 构造蓝图
            blueprint = ExecutionBlueprint(
                blueprint_id=f"sub_{call_spec.id}",
                target_service=call_spec.agent_id,
                task=TaskSpec(instruction=call_spec.instruction),
                resource=ResourceSpec(artifact_refs=call_spec.artifact_refs),
                output=OutputSpec()
            )
            
            final_output = ""
            try:
                async for event in self.execute_task(
                    agent_id=call_spec.agent_id,
                    instruction=call_spec.instruction,
                    session_id=session_id,
                    blueprint=blueprint
                ):
                    # 实时将子任务事件推入汇总队列
                    await queue.put(event)
                    if event["type"] == "conclusion":
                        final_output = event["content"]
                    elif event["type"] == "error":
                        final_output = f"Error: {event['content']}"
                
                await queue.put({"task_id": call_spec.id, "status": "success", "output": final_output})
            except Exception as e:
                await queue.put({"task_id": call_spec.id, "status": "error", "output": str(e)})
            finally:
                pending_tasks -= 1
                if pending_tasks == 0:
                    await queue.put(None) # 终止标识

        # 启动并行协程
        for c in calls:
            asyncio.create_task(_run_and_collect(c))

        # 扇入聚合与实时冒泡
        raw_results = {}
        while True:
            item = await queue.get()
            if item is None:
                break
            
            # 区分过程事件与结果数据
            if "type" in item:
                yield item # 冒泡过程事件 (stream, status, etc.)
            else:
                # 收集用于聚合的结果
                raw_results[item["task_id"]] = {
                    "status": item["status"],
                    "output": item["output"]
                }

        # 最终产出脱水聚合报告
        aggregation = ResultAggregator.aggregate(session_id, raw_results)
        yield {"type": "observation", "content": aggregation}

dispatcher = Dispatcher()
