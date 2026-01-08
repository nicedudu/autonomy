"""
分布式聚合引擎 (Aggregator V3.5)

职责：对子任务产出进行脱水存储与结构化反馈。
核心机制：
1. 建立基于 ID 的引用传递映射。
2. 将执行失败翻译为“逻辑层”可理解的诊断观测。
3. 确保数据流的原子性与零损耗。
"""

import json
from typing import Any, Dict
from core.agent.memory import memory_gateway
from core.utils.logging import logger

class ResultAggregator:
    """聚合与脱水中心。"""

    @staticmethod
    def aggregate(session_id: str, raw_results: Dict[str, Any]) -> str:
        """
        [扇入聚合] 执行结论脱水并生成观测报告。
        """
        report = {}

        for task_id, res in raw_results.items():
            status = res.get("status")
            output = res.get("output")
            error_msg = res.get("message")

            if status == "success" and output:
                # 正常分支：产物脱水入库
                try:
                    artifact_id = memory_gateway.store(
                        session_id=session_id,
                        content=output,
                        art_type="task_conclusion",
                        metadata={"source_task": task_id}
                    )
                    report[task_id] = {
                        "state": "success",
                        "artifact_ref": artifact_id,
                        "summary": str(output)[:100] + "..." if len(str(output)) > 100 else str(output)
                    }
                    logger.debug(f"子任务 [{task_id}] 聚合成功 -> {artifact_id}", "Aggregator")
                except Exception as e:
                    logger.error(f"子任务 [{task_id}] 脱水失败: {str(e)}", "Aggregator")
                    report[task_id] = {"state": "error", "error_detail": "产物同步至内存网关时发生异常"}
            else:
                # 异常分支：诊断性封装
                final_error = error_msg or "子任务结论缺失（可能发生了逻辑死循环）"
                report[task_id] = {
                    "state": "error",
                    "error_detail": final_error,
                    "can_retry": True
                }
                logger.warning(f"子任务 [{task_id}] 执行异常: {final_error}", "Aggregator")

        # 生成符合协议的标准 Observation 载荷
        return json.dumps({
            "observation_type": "execution_report",
            "task_results": report
        }, ensure_ascii=False)