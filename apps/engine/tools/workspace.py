"""
工作空间管理工具 (Workspace Management)

提供对受控文件系统的访问能力，包含列表审计、读取与持久化操作。
所有操作均强制执行根目录边界校验，确保数据安全隔离。
"""

import os
from typing import Any, Dict, List

from core.tools.base import tool


class WorkspaceManager:
    """
    工作空间核心服务。
    实现路径归一化与安全边界审计。
    """

    def __init__(self, root: str = "."):
        self.root = os.path.abspath(root)

    def _get_safe_path(self, rel_path: str) -> str:
        """解析安全路径，防止目录遍历攻击。"""
        safe_path = os.path.abspath(os.path.join(self.root, rel_path))
        if not safe_path.startswith(self.root):
            raise PermissionError(f"越界访问被拒绝: {rel_path}")
        return safe_path

    def list_entries(self, dir_path: str) -> List[str]:
        """列出目录条目。"""
        path = self._get_safe_path(dir_path)
        if not os.path.exists(path):
            return []
        return os.listdir(path)


# 全局工作空间实例
_ws = WorkspaceManager()


@tool()
async def list_workspace_files(directory: str = ".") -> Dict[str, Any]:
    """
    列出当前工作空间指定目录下的所有文件与子目录。
    用于探索项目结构或确认文件存在性。

    Args:
        directory: 目标目录的相对路径，默认为根目录 "."。
    """
    try:
        entries = _ws.list_entries(directory)
        return {
            "status": "success",
            "directory": directory,
            "entries": entries,
            "count": len(entries)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@tool()
async def read_workspace_file(file_path: str) -> Dict[str, Any]:
    """
    从工作空间中读取指定文件的完整文本内容。

    Args:
        file_path: 文件的相对路径。
    """
    try:
        full_path = _ws._get_safe_path(file_path)
        if not os.path.isfile(full_path):
            return {"status": "error", "message": f"路径 '{file_path}' 不是一个有效文件。"}

        with open(full_path, "r", encoding="utf-8") as f:
            return {
                "status": "success",
                "content": f.read(),
                "file_path": file_path
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@tool()
async def write_workspace_file(file_path: str, content: str) -> Dict[str, Any]:
    """
    在工作空间中创建或覆盖指定文件。
    自动处理缺失的中间目录。

    Args:
        file_path: 写入的目标相对路径。
        content: 写入的文本内容。
    """
    try:
        full_path = _ws._get_safe_path(file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

        return {
            "status": "success",
            "message": f"成功写入文件: {file_path}",
            "bytes": len(content)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
