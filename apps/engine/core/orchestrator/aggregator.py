"""
结果聚合引擎 (Result Aggregator)

执行分布式任务产出的标准化聚合。
支持对成功产物的脱水映射及对失败任务的诊断性封装，确认为主脑提供确定性的观测反馈。
"""

import json
from typing import Any, Dict
from core.agent.memory import memory_gateway

class ResultAggregator:
    """
    任务结果聚合器。
    
    实现扇入逻辑，将多并行的子任务状态转化为结构化的环境观测值。
    """

    @staticmethod
    def aggregate(session_id: str, raw_results: Dict[str, Any]) -> str:
        """
        执行结果的脱水聚合与诊断封装。
        
        Args:
            session_id: 当前会话标识符。
            raw_results: 原始执行结果映射。
            
        Returns:
            str: 符合 JSON 协议的结构化观测载荷。
        """
        report = {}

        for task_id, res in raw_results.items():
            status = res.get("status")
            output = res.get("output")

            if status == "success":
                # 正常产物脱水处理
                artifact_id = memory_gateway.store(
                    session_id=session_id,
                    content=output,
                    art_type="task_conclusion",
                    metadata={"source_task": task_id}
                )
                report[task_id] = {
                    "state": "success",
                    "artifact_ref": artifact_id,
                    "summary": str(output)[:150] + "..." if len(str(output)) > 150 else str(output)
                }
            else:
                # 异常诊断封装：提供详细错误原因，引导主脑反思
                report[task_id] = {
                    "state": "error",
                    "error_detail": res.get("message", "执行单元发生非预期中断"),
                    "can_retry": True # 标识该错误是否具备重试价值
                }

        return json.dumps({
            "observation_type": "execution_report",
            "task_results": report
        }, ensure_ascii=False)