import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from api.routes import agent, chat
from api.utils import manager, emit_event
from api.deps import dispatcher

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    管理应用程序的生命周期。
    """
    # --- 启动逻辑：各领域自举发现 ---
    from core.agent.registry import agent_registry
    from core.tools.registry import tool_registry
    
    # 打印能力清单进行初始化审计
    print(f"[Lifespan] 系统能力自举完成:")
    print(f"  - 可用智能体: {agent_registry.get_agents()}")
    
    def bus_to_ui_callback(message):
        """将内部总线消息实时转发至 WebSocket 发送队列。"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(emit_event("agent_message", message.model_dump()))
        except Exception:
            pass

    # 绑定回调
    dispatcher.bus.set_on_message_callback(bus_to_ui_callback)
    
    yield
    
    # --- 关闭逻辑 ---
    dispatcher.bus.set_on_message_callback(None)

def create_app() -> FastAPI:
    """
    初始化并配置 FastAPI 应用程序。
    """
    app = FastAPI(title="Autonomy Engine API", version="4.0.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(agent.router)
    app.include_router(chat.router)

    @app.websocket("/ws/ops")
    async def websocket_endpoint(websocket: WebSocket):
        """实时运维 WebSocket 入口。"""
        await manager.connect(websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            manager.disconnect(websocket)

    return app

app = create_app()
