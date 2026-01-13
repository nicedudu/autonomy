import io
import sys
import traceback
from typing import Any, Dict

from core.tools.base import tool


class CodeSandbox:
    """
    Python 代码安全执行沙箱封装。
    用于后续对接隔离环境（如 Docker/WASM）。
    """

    @staticmethod
    async def run(code: str) -> Dict[str, Any]:
        """
        在本地受限环境中执行代码，并捕获标准输出。
        """
        output_buffer = io.StringIO()
        original_stdout = sys.stdout
        sys.stdout = output_buffer

        execution_locals = {}

        try:
            # 内部执行逻辑。生产环境建议通过隔离服务调用。
            exec(code, {"__builtins__": __builtins__}, execution_locals)
            sys.stdout = original_stdout

            result_output = output_buffer.getvalue()

            if not result_output and "result" in execution_locals:
                result_output = str(execution_locals["result"])

            return {
                "status": "success",
                "output": result_output or "代码执行成功，无输出。"
            }
        except Exception:
            sys.stdout = original_stdout
            return {
                "status": "error",
                "message": traceback.format_exc()
            }


@tool(name="python_execute")
async def python_execute(code: str) -> Dict[str, Any]:
    """
    执行 Python 代码并返回输出或错误。
    适用于数据分析、数学计算和逻辑验证。

    code: 需要执行的完整 Python 代码块。
    """
    return await CodeSandbox.run(code)
