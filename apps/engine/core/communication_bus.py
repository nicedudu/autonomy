
import asyncio
import time
import uuid
from typing import Dict, List, Optional, Any, Callable

class CommunicationBus:
    """
    Agent 间通信与状态广播中枢。
    采用异步 Pub/Sub 模式，支持 WebSocket 多客户端实时监听。
    """

    def __init__(self):
        self._subscribers: List[asyncio.Queue] = []
        self.agents = {}
        self.meetings = {}
        self.message_history = []
        self.on_message_callback: Optional[Callable] = None

    def subscribe(self) -> asyncio.Queue:
        """订阅总线事件。"""
        queue = asyncio.Queue()
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        """取消订阅。"""
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    async def publish(self, event_type: str, payload: Any):
        """
        发布广播事件。
        所有通过 WebSocket 连接的客户端都会收到此事件。
        """
        event = {
            "type": event_type,
            "payload": payload,
            "timestamp": time.time()
        }
        
        # 1. 异步分发给所有订阅队列
        tasks = []
        for queue in self._subscribers:
            tasks.append(queue.put(event))
        
        if tasks:
            # 采用 wait 防止单个订阅者延迟拖慢整个系统
            await asyncio.gather(*tasks, return_exceptions=True)

        # 2. 兼容旧版回调逻辑
        if self.on_message_callback:
            self.on_message_callback(event)

    def set_on_message_callback(self, callback: Callable):
        self.on_message_callback = callback

    # 保留原有的 Agent 注册逻辑以便兼容性
    def register_agent(self, agent):
        self.agents[agent.agent_id] = agent
        
    async def send_message(self, message: Any) -> bool:
        # 兼容旧版消息发送
        self.message_history.append(message)
        await self.publish("message_sent", message if hasattr(message, "model_dump") else message)
        return True

# 全局总线单例
bus = CommunicationBus()
