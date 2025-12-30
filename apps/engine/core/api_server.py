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
from agents.ceo_agent import CEOAgent
from agents.cpo_agent import CPOAgent
from agents.scm_agent import SCMAgent

app = FastAPI(title="Autonomy Control Plane")

# 允许跨域，方便 Next.js 访问
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
    # 使用 asyncio.create_task 触发异步广播
    # 注意：在 FastAPI 中需要确保在事件循环运行期间调用
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(emit_event("agent_message", message.model_dump()))
    except Exception as e:
        print(f"转发总线消息到 UI 失败: {e}")

orchestrator.bus.set_on_message_callback(bus_to_ui_callback)

agent_instances: Dict[str, Any] = {}
supabase_manager = SupabaseManager()

def get_agent_instance(agent_id: str):
    if agent_id not in agent_instances:
        # 从 Supabase 获取配置以确认 Agent 存在并获取基本信息
        config = supabase_manager.get_agent_config(agent_id)
        if not config:
            raise ValueError(f"智能体 {agent_id} 未在数据库中配置")
        
        name = config.get("name", "智能助手")
        
        agent = None
        # 根据 identifier 决定使用的类
        if "ceo" in agent_id:
            agent = CEOAgent(agent_id=agent_id, name=name)
        elif "cpo" in agent_id:
            agent = CPOAgent(agent_id=agent_id, name=name)
        elif "scm" in agent_id:
            agent = SCMAgent(agent_id=agent_id, name=name)
        else:
            # 默认使用 BaseAgent
            from agents.base_agent import BaseAgent
            agent = BaseAgent(agent_id=agent_id, agent_type="general", name=name)
        
        if agent:
            orchestrator.register_agent(agent)
            agent_instances[agent_id] = agent
            
    return agent_instances[agent_id]

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

@app.post("/api/chat/stream")
async def chat_stream(request: Dict[str, Any]):
    """流式对话接口"""
    agent_id = request.get("agent_id", "ceo_agent")
    content = request.get("content", "")
    
    agent = get_agent_instance(agent_id)
    
    async def event_generator():
        # print(f"DEBUG: [Server层] 开始流式推送，Agent: {agent_id}")
        async for chunk in agent.chat_stream_async(content):
            yield chunk

    return StreamingResponse(event_generator(), media_type="text/plain")

@app.get("/api/agents")
async def get_agents():
    """获取所有在线 Agent 列表"""
    try:
        response = supabase_manager.client.table("agents").select("*").execute()
        return response.data
    except Exception as e:
        print(f"获取智能体列表失败: {e}")
        return []


@app.post("/api/prompts/save")
async def save_prompts(config: Dict[str, Any]):
    """从前端保存修改后的 Prompt"""
    with open("prompts/library.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, allow_unicode=True)
    return {"status": "success"}

@app.post("/api/chat/summarize")
async def summarize_chat(request: Dict[str, Any]):
    """生成会话总结标题"""
    content = request.get("content", "")
    if not content:
        return {"title": "新会话"}
    
    try:
        # 获取专用总结提示词
        with open("prompts/library.yaml", "r", encoding="utf-8") as f:
            lib = yaml.safe_load(f)
            summarizer_config = lib.get("utils", {}).get("summarizer", {})
            system_prompt = summarizer_config.get("system", "Summarize the following into a short title.")

        # 统一使用全局通用 LLM 配置执行总结任务
        llm_factory = LLMFactory()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ]
        response = llm_factory.call_default_llm(messages)
        summary = response.content
        
        title = summary.strip().strip('"').strip("'")
        if len(title) > 50:
            title = title[:47] + "..."
            
        return {"title": title}
    except Exception as e:
        print(f"总结失败: {e}")
        return {"title": "新会话"}

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
