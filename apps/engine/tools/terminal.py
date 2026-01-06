import asyncio
from typing import Dict, Any
from tools.base import tool

class TerminalService:
    """
    终端命令异步执行服务。
    处理子进程生命周期与输出捕获。
    """

    @staticmethod
    async def execute(command: str) -> Dict[str, Any]:
        """
        启动 shell 进程并执行命令，同时捕获 stdout 与 stderr。
        """
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            output_str = stdout.decode().strip()
            error_str = stderr.decode().strip()
            
            combined_output = []
            if output_str:
                combined_output.append(output_str)
            if error_str:
                combined_output.append(f"错误输出:\n{error_str}")
            
            return {
                "status": "success",
                "output": "\n".join(combined_output) if combined_output else "命令成功执行，无输出。"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"执行失败: {str(e)}"
            }

@tool(name="terminal_execute")
async def terminal_execute(command: str) -> Dict[str, Any]:
    """
    执行终端命令并返回输出。
    
    command: 需要执行的 shell 命令字符串。
    """
    return await TerminalService.execute(command)
