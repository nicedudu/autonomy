"""
任务编排调度中枢 (Dispatcher V3.5)

职责：管理分布式任务的扇出 (Fan-out) 与扇入 (Fan-in)。
核心机制：
1. 实现子任务的并发隔离执行。
2. 汇聚并冒泡所有子节点的实时事件流。
3. 确保子任务结论的完整性捕获。
"""

import asyncio
from typing import Any, AsyncGenerator, Dict, List, Optional
from core.protocol.schema import ProtocolCall
from core.orchestrator.aggregator import ResultAggregator
from core.communication_bus import bus
from core.schema.collaboration import ExecutionBlueprint, TaskSpec, ResourceSpec, OutputSpec
from core.utils.logging import logger

class Dispatcher:
    """任务调度中心。"""

    def __init__(self):
        self.bus = bus

    async def execute_task(
        self,
        agent_id: str,
        instruction: str,
        session_id: str,
        blueprint: Optional[ExecutionBlueprint] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """[原子调度] 驱动单节点的生命周期。"""
        from core.agent.factory import ExecutionUnitFactory
        
        # JIT 实例化执行单元
        runtime = ExecutionUnitFactory.create_runtime(agent_id, session_id, blueprint)
        
        # 实时穿透子任务事件流
        async for event in runtime.run(input_text=instruction, blueprint=blueprint, session_id=session_id):
            yield event

    async def dispatch_calls(
        self,
        calls: List[ProtocolCall],
        session_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        [并发分发] 执行扇出调度并实现事件冒泡汇聚。
        
        采用异步生产-消费模型，确保多节点输出互不阻塞。
        """
        if not calls:
            yield {"type": "observation", "content": "{}"}
            return

        queue = asyncio.Queue()
        active_task_count = len(calls)

        async def _worker(call_spec: ProtocolCall):
            nonlocal active_task_count
            # 1. 契约转化：ProtocolCall -> ExecutionBlueprint
            blueprint = ExecutionBlueprint(
                blueprint_id=f"sub_{call_spec.id}",
                target_service=call_spec.agent_id,
                task=TaskSpec(instruction=call_spec.instruction),
                resource=ResourceSpec(artifact_refs=call_spec.artifact_refs),
                output=OutputSpec()
            )
            
            task_result = {"task_id": call_spec.id, "status": "success", "output": None, "message": None}
            
            try:
                # 2. 启动执行并冒泡事件
                async for event in self.execute_task(call_spec.agent_id, call_spec.instruction, session_id, blueprint):
                    # 标识事件来源以便 UI 区分
                    event["source_task"] = call_spec.id
                    await queue.put(event)
                    
                    if event["type"] == "conclusion":
                        task_result["output"] = event["content"]
                    elif event["type"] == "error":
                        task_result["status"] = "error"
                        task_result["message"] = event["content"]
                
                # 3. 结果完整性自检
                if task_result["status"] == "success" and not task_result["output"]:
                    task_result["status"] = "error"
                    task_result["message"] = "执行单元未产出有效结论载荷"
                    
            except Exception as e:
                task_result["status"] = "error"
                task_result["message"] = f"调度层非预期中断: {str(e)}"
            finally:
                # 将最终处理后的结果放入队列
                await queue.put(task_result)
                active_task_count -= 1
                if active_task_count == 0:
                    await queue.put(None) # 终止标识

        # 启动并发协程
        for call in calls:
            asyncio.create_task(_worker(call))

        # 实时消费并汇总结果
        raw_results = {}
        while True:
            item = await queue.get()
            if item is None: break
            
            if "type" in item:
                yield item # 向上传播过程事件
            else:
                # 收集用于扇入聚合的结论数据
                raw_results[item["task_id"]] = {
                    "status": item["status"],
                    "output": item["output"],
                    "message": item["message"]
                }

        # 4. 执行扇入聚合 (Fan-in)
        aggregation_report = ResultAggregator.aggregate(session_id, raw_results)
        yield {"type": "observation", "content": aggregation_report}

dispatcher = Dispatcher()
