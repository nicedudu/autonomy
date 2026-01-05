import importlib.util
import asyncio
import os
from typing import Any, Dict
from core.schema.models import ActionResult, Status

class ToolRunner:
    """
    动态工具执行引擎。
    负责热加载 tools/ 目录下的 Python 脚本并执行，支持同步与异步兼容调用。
    """

    def __init__(self):
        # 定位工具根目录
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        self.tools_dir = os.path.join(os.path.dirname(os.path.dirname(current_file_dir)), "tools")

    async def run(self, tool_name: str, params: Dict[str, Any]) -> ActionResult:
        """物理加载并运行指定工具。"""
        file_path = os.path.join(self.tools_dir, f"{tool_name}.py")
        
        if not os.path.exists(file_path):
            return ActionResult(status=Status.FAILED, error=f"工具不存在: {tool_name}")

        try:
            # 模块热加载
            module_name = f"runtime.impl.{tool_name}"
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if not hasattr(module, "run"):
                return ActionResult(status=Status.FAILED, error="工具未实现 run 接口")

            # 兼容性调用
            raw_result = await module.run(params) if asyncio.iscoroutinefunction(module.run) else module.run(params)
            
            # 结果标准化
            status = Status.SUCCESS
            if isinstance(raw_result, dict) and (raw_result.get("status") == "error" or raw_result.get("success") is False):
                status = Status.FAILED
            
            return ActionResult(
                status=status,
                output=raw_result.get("output") or raw_result.get("result") or str(raw_result),
                error=raw_result.get("message") or raw_result.get("error"),
                tool_name=tool_name
            )
        except Exception as e:
            return ActionResult(status=Status.FAILED, error=f"执行异常: {str(e)}")
