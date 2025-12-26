import asyncio
import json
import yaml
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any

app = FastAPI(title="Autonomy Control Plane")

# 允许跨域，方便 Next.js 访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    """管理 WebSocket 连接，实现实时广播"""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """向所有前端页面发送数据"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

@app.get("/api/prompts")
async def get_prompts():
    """读取 Prompt 库供前端展示"""
    with open("prompts/library.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

@app.get("/api/config/agents")
async def get_agent_config():
    """读取 Agent 详细配置"""
    with open("config/agents.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

@app.post("/api/config/agents/save")
async def save_agent_config(config: Dict[str, Any]):
    """保存 Agent 详细配置"""
    with open("config/agents.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, allow_unicode=True)
    return {"status": "success"}

@app.get("/api/agents")
async def get_agents():
    """获取所有在线 Agent 列表"""
    # 在实际运行中，Orchestrator 会持有这些信息
    # 这里先返回模拟数据，实际应从全局单例获取
    return [
        {
            "id": "ceo_agent",
            "name": "CEO - 战略中心",
            "type": "ceo",
            "status": "active",
            "last_output": "正在监控 Q4 环保趋势项目...",
            "avatar": "🦁"
        },
        {
            "id": "cpo_agent",
            "name": "CPO - 选品官",
            "type": "cpo",
            "status": "busy",
            "last_output": "已识别 5 个爆款潜力 SKU",
            "avatar": "🔍"
        },
        {
            "id": "scm_agent",
            "name": "SCM - 供应链",
            "type": "scm",
            "status": "idle",
            "last_output": "1688 供应商报价已更新",
            "avatar": "📦"
        },
        {
            "id": "cmo_agent",
            "name": "CMO - 营销官",
            "type": "cmo",
            "status": "active",
            "last_output": "TikTok 广告投放策略已生成",
            "avatar": "📢"
        }
    ]

@app.post("/api/prompts/save")
async def save_prompts(config: Dict[str, Any]):
    """从前端保存修改后的 Prompt"""
    with open("prompts/library.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, allow_unicode=True)
    return {"status": "success"}

@app.websocket("/ws/ops")
async def websocket_endpoint(websocket: WebSocket):
    """运营数据实时流"""
    await manager.connect(websocket)
    try:
        while True:
            # 保持连接，等待心跳或来自客户端的消息
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# 工具函数：供后端其他组件调用以推送数据
async def emit_event(event_type: str, data: Any):
    await manager.broadcast({
        "type": event_type,
        "data": data,
        "timestamp": json.dumps(data.get("timestamp")) if isinstance(data, dict) else None
    })
