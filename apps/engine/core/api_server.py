import asyncio
import json
import yaml
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any

from core.supabase_manager import SupabaseManager
from core.orchestrator import Orchestrator
from core.llm_factory import LLMFactory
from core.registry.manager import discovery_service

app = FastAPI(title="Autonomy Control Plane")

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化全局编排器
orchestrator = Orchestrator()

# 将通信总线的消息转发到 WebSocket 广播
def bus_to_ui_callback(message):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(emit_event("agent_message", message.model_dump()))
    except Exception as e:
        print(f"转发总线消息到 UI 失败: {e}")

orchestrator.bus.set_on_message_callback(bus_to_ui_callback)

supabase_manager = SupabaseManager()

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
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

@app.get("/api/prompts")
async def get_prompts():
    """获取云端全局提示词配置 (Nexus V4)"""
    try:
        settings = supabase_manager.get_system_settings()
        return {
            "core_system_prompt": settings.get("core_system_prompt", ""),
            "default_model": settings.get("default_model", "")
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/prompts/save")
async def save_prompts(config: Dict[str, Any]):
    """将前端修改后的 Prompt 保存到云端数据库"""
    try:
        core_prompt = config.get("core_system_prompt")
        if core_prompt:
            supabase_manager.client.table("system_settings").update({
                "core_system_prompt": core_prompt,
                "updated_at": "now()"
            }).eq("id", 1).execute()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/chat/stream")
async def chat_stream(request: Dict[str, Any]):
    """
    [Nexus V4] Universal Stream Interface.
    """
    agent_id = request.get("agent_id", "primary_agent")
    content = request.get("content", "")
    
    async def event_generator():
        async for event in orchestrator.dispatch(agent_id, content):
            yield json.dumps(event) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

@app.get("/api/agents")
async def get_agents():
    """获取注册中心所有在线 Agent 列表 (Nexus V4)"""
    try:
        manifests = discovery_service.agents.all()
        return [
            {
                "id": m.agent_id,
                "identifier": m.agent_id,
                "name": m.name,
                "role": m.role,
                "model": m.model,
                "system_prompt": m.system_prompt_template,
                "is_manifest": True,
                "avatar": f"https://api.dicebear.com/7.x/avataaars/svg?seed={m.name}"
            }
            for m in manifests.values()
        ]
    except Exception as e:
        print(f"获取智能体列表失败: {e}")
        return []

@app.get("/api/skills")
async def get_skills():
    """获取所有可用技能清单"""
    try:
        skills = discovery_service.skills.all()
        return [
            {
                "id": s.skill_id,
                "name": s.name,
                "description": s.description,
                "parameters": s.parameters,
                "implementation": s.implementation
            }
            for s in skills.values()
        ]
    except Exception as e:
        return []

@app.post("/api/chat/summarize")
async def summarize_chat(request: Dict[str, Any]):
    """生成会话总结标题 (严格数据库驱动)"""
    content = request.get("content", "")
    if not content:
        return {"title": "新会话"}
    
    try:
        llm_factory = LLMFactory()
        system_prompt = "You are a professional secretary. Summarize the user's intent into a title under 10 words. Chinese if the input is Chinese."
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ]
        response = llm_factory.call_default_llm(messages)
        summary = response.content
        title = summary.strip().strip('"').strip("'")
        if len(title) > 50: title = title[:47] + "..."
        return {"title": title}
    except Exception as e:
        return {"title": "新会话"}

@app.websocket("/ws/ops")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def emit_event(event_type: str, data: Any):
    await manager.broadcast({
        "type": event_type,
        "data": data,
        "timestamp": json.dumps(data.get("timestamp")) if isinstance(data, dict) else None
    })