
import asyncio
import json
import time
from typing import List, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from core.communication_bus import bus

router = APIRouter(prefix="/ws", tags=["WebSocket"])

class ConnectionManager:
    """WebSocket 连接管理器"""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

@router.websocket("/control-panel/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    Agent 执行控制面板专用 Socket。
    """
    await manager.connect(websocket)
    
    # 获取总线订阅队列
    queue = bus.subscribe()
    
    try:
        # 1. 尝试从缓存恢复当前会话的最新快照
        from core.session.manager import session_manager
        session = session_manager.get_session(session_id)
        if session:
            local_nodes = session.get_metadata("session_blueprint_nodes", {})
            if local_nodes:
                await websocket.send_json({
                    "type": "execution_snapshot",
                    "payload": {
                        "session_id": session_id,
                        "nodes": list(local_nodes.values())
                    }
                })
                # 同时尝试恢复拓扑结构
                await websocket.send_json({
                    "type": "topology_update",
                    "payload": {
                        "session_id": session_id,
                        "blueprint": {"nodes": list(local_nodes.values())}
                    }
                })

        # 2. 发送建立连接确认
        await websocket.send_json({
            "type": "connection_established",
            "session_id": session_id,
            "server_time": time.time()
        })

        # 启动后台监听任务
        while True:
            # 使用 wait_for 增加超时控制，防止死等
            try:
                # 监听总线事件
                event = await asyncio.wait_for(queue.get(), timeout=1.0)
                
                # 过滤逻辑：只推送当前 Session 相关或全局事件
                # 在生产环境下，payload 中应包含 session_id
                payload = event.get("payload", {})
                event_session_id = payload.get("session_id") if isinstance(payload, dict) else None
                
                if not event_session_id or event_session_id == session_id:
                    print(f"\033[94m[WS Push] Type: {event['type']} | Session: {session_id}\033[0m")
                    await websocket.send_json(event)
                
                queue.task_done()
            except asyncio.TimeoutError:
                # 超时则发送心跳，保持连接活跃
                await websocket.send_json({"type": "ping", "time": time.time()})
                continue

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    finally:
        bus.unsubscribe(queue)
        manager.disconnect(websocket)
