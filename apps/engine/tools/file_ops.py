import os
from typing import Dict, Any
from core.tools.base import tool

class FileSystemManager:
    """
    文件系统安全操作服务。
    强制执行目录边界约束，并提供标准化的错误处理。
    """
    
    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)

    def _get_safe_path(self, relative_path: str) -> str:
        """解析并验证目标路径是否在工作区范围内。"""
        target_path = os.path.abspath(os.path.join(self.root_dir, relative_path))
        if not target_path.startswith(self.root_dir):
            raise PermissionError("访问受限：目标路径超出工作区边界。")
        return target_path

    def list_dir(self, path: str = ".") -> Dict[str, Any]:
        """列出目录内容。"""
        try:
            target = self._get_safe_path(path)
            if not os.path.exists(target):
                return {"status": "error", "message": f"路径 '{path}' 不存在。"}
            
            items = os.listdir(target)
            return {"status": "success", "output": "\n".join(items) if items else "目录为空。"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def read(self, file_path: str) -> Dict[str, Any]:
        """读取文件内容。"""
        try:
            target = self._get_safe_path(file_path)
            if not os.path.isfile(target):
                return {"status": "error", "message": f"'{file_path}' 不是有效文件。"}
            
            with open(target, "r", encoding="utf-8") as f:
                return {"status": "success", "output": f.read()}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def write(self, file_path: str, content: str) -> Dict[str, Any]:
        """写入或覆盖文件内容。"""
        try:
            target = self._get_safe_path(file_path)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)
            return {"status": "success", "output": f"成功写入文件: {file_path}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

# 全局单例，锚定当前工作目录。
fs_service = FileSystemManager(os.getcwd())

@tool(name="list_files")
async def list_files(path: str = ".") -> Dict[str, Any]:
    """
    列出指定路径下的文件和目录。
    
    path: 相对路径。默认为当前目录 "."。
    """
    return fs_service.list_dir(path)

@tool(name="read_file")
async def read_file(file_path: str) -> Dict[str, Any]:
    """
    读取指定文件的内容。
    
    file_path: 文件的相对路径。
    """
    return fs_service.read(file_path)

@tool(name="write_file")
async def write_file(file_path: str, content: str) -> Dict[str, Any]:
    """
    向指定文件写入内容。
    
    file_path: 文件的相对路径。
    content: 写入的字符串内容。
    """
    return fs_service.write(file_path, content)
