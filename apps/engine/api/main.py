import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from api.routes import agent, chat
from api.utils import manager, emit_event

def create_app() -> FastAPI:
    """
    初始化并配置 FastAPI 应用程序。
    包含中间件、路由挂载以及事件总线回调的绑定。
    """
    app = FastAPI(title="Autonomy Engine API", version="4.0.0")

    # 配置跨域资源共享
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 挂载业务路由
    app.include_router(agent.router)
    app.include_router(chat.router)

    # 绑定总线回调：将系统内部消息实时转发至 UI
    def bus_to_ui_callback(message):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(emit_event("agent_message", message.model_dump()))
        except Exception:
            pass

    # 注入回调到全局编排器（从 chat 模块复用实例）
    chat.orchestrator.bus.set_on_message_callback(bus_to_ui_callback)

    @app.websocket("/ws/ops")
    async def websocket_endpoint(websocket: WebSocket):
        """实时运维 WebSocket 入口。"""
        await manager.connect(websocket)
        try:
            while True:
                # 维持连接，接受心跳
                await websocket.receive_text()
        except WebSocketDisconnect:
            manager.disconnect(websocket)

    return app

# 全局 App 实例
app = create_app()
