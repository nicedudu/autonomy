import asyncio
import json
import yaml
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any

from core.supabase_manager import SupabaseManager
from core.orchestrator import Orchestrator
from core.registry.manager import discovery_service

app = FastAPI(title="Autonomy Engine API", version="4.0.0")

# Cross-Origin Resource Sharing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Orchestrator Instance
orchestrator = Orchestrator()

# Broadcast Bus messages to UI via WebSocket
def bus_to_ui_callback(message):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(emit_event("agent_message", message.model_dump()))
    except Exception as e:
        print(f"[Bus] Failed to forward message to UI: {e}")

orchestrator.bus.set_on_message_callback(bus_to_ui_callback)

supabase_manager = SupabaseManager()

class ConnectionManager:
    """Manages real-time WebSocket connections."""
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

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "4.0.0"}

@app.get("/api/agents")
async def get_agents():
    """Returns all agents from the local registry, synced with DB metadata."""
    try:
        # Re-initialize to ensure fresh manifest data
        discovery_service.initialize()
        manifests = discovery_service.agents.all()
        return [
            {
                "id": m.agent_id,
                "identifier": m.agent_id,
                "name": m.name,
                "role": m.role,
                "description": m.description,
                "capabilities": m.capabilities,
                "model": m.model,
                "system_prompt": m.system_prompt_template,
                "avatar": f"https://api.dicebear.com/7.x/avataaars/svg?seed={m.agent_id}"
            }
            for m in manifests.values()
        ]
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/skills")
async def get_skills():
    """Returns available specialized capabilities from registry."""
    try:
        discovery_service.initialize()
        skills = discovery_service.skills.all()
        return [
            {
                "id": skill_id,
                "name": s.name,
                "description": s.description,
                "metadata": s.metadata,
                "instructions": s.instructions
            }
            for skill_id, s in skills.items()
        ]
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/chat/summarize")
async def summarize_chat(request: Dict[str, Any]):
    """Generates a short session title based on user input."""
    content = request.get("content", "")
    if not content:
        return {"title": "新会话"}
    
    try:
        from core.llm_factory import LLMFactory
        llm_factory = LLMFactory()
        system_prompt = "You are a specialized secretary. Summarize the user's intent into a title under 10 words. Answer in the same language as the user input."
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ]
        response = llm_factory.call_default_llm(messages)
        title = response.content.strip().strip('"').strip("'")
        if len(title) > 50: title = title[:47] + "..."
        return {"title": title}
    except Exception as e:
        print(f"[API] Summarize error: {e}")
        return {"title": "新会话"}

@app.post("/api/chat/stream")
async def chat_stream(request: Dict[str, Any]):
    """Unified streaming execution endpoint."""
    agent_id = request.get("agent_id", "primary_agent")
    content = request.get("content", "")
    
    async def event_generator():
        async for event in orchestrator.dispatch(agent_id, content):
            yield json.dumps(event) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

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
