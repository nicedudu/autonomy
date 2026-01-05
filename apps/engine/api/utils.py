from typing import Any, Dict, List
from fastapi import WebSocket
import json

class ConnectionManager:
    """
    管理实时 WebSocket 连接。
    负责维护活跃连接、安全断开以及消息广播。
    """

    def __init__(self):
        # 活跃连接列表
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """接受并记录新的连接。"""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """移除已断开的连接。"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """向所有活跃客户端广播 JSON 消息。"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # 忽略发送失败的连接
                pass

# 全局连接管理器单例
manager = ConnectionManager()

async def emit_event(event_type: str, data: Any):
    """
    格式化并广播事件。
    
    Args:
        event_type: 事件类型（如 agent_message）。
        data: 事件携带的数据负载。
    """
    await manager.broadcast({
        "type": event_type,
        "data": data,
        "timestamp": json.dumps(data.get("timestamp")) if isinstance(data, dict) else None
    })
