from typing import Any, Dict, List, Optional, Callable
from core.schema.models import Message

class MeetingRoom:
    """数字会议室"""
    
    def __init__(self, meeting_id: str, topic: str, organizer: str):
        self.meeting_id = meeting_id
        self.topic = topic
        self.organizer = organizer
        self.participants = []
        self.messages = []
        self.start_time = None
        self.end_time = None
        self.status = "created"  # created, in_progress, completed
    
    def add_participant(self, agent_id: str):
        """添加参会者"""
        if agent_id not in self.participants:
            self.participants.append(agent_id)
    
    def remove_participant(self, agent_id: str):
        """移除参会者"""
        if agent_id in self.participants:
            self.participants.remove(agent_id)
    
    def add_message(self, message: Message):
        """添加会议消息"""
        self.messages.append(message)
    
    def start(self):
        """开始会议"""
        self.status = "in_progress"
    
    def end(self):
        """结束会议"""
        self.status = "completed"
    
    def get_summary(self) -> Dict:
        """获取会议总结"""
        return {
            "meeting_id": self.meeting_id,
            "topic": self.topic,
            "organizer": self.organizer,
            "participants": self.participants,
            "message_count": len(self.messages),
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time
        }

class CommunicationBus:
    """Agent间通信中枢"""
    
    def __init__(self):
        self.agents = {}  # agent_id -> agent_instance
        self.meetings = {}  # meeting_id -> meeting_instance
        self.message_history = []
        self.message_queue = []
        self.on_message_callback = None
    
    def set_on_message_callback(self, callback):
        """设置消息回调，用于对接 UI 或外部监控"""
        self.on_message_callback = callback

    def register_agent(self, agent):
        """注册Agent"""
        self.agents[agent.agent_id] = agent
        print(f"通信中枢: 已注册Agent {agent.name} ({agent.agent_id})")
    
    def unregister_agent(self, agent_id: str):
        """注销Agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            print(f"通信中枢: 已注销Agent {agent_id}")

    async def send_message(self, message: Message) -> bool:
        """发送消息"""
        self.message_history.append(message)
        
        # 触发回调
        if self.on_message_callback:
            try:
                self.on_message_callback(message)
            except Exception as e:
                print(f"通信中枢回调执行失败: {e}")

        # 私聊模式
        if message.message_type == "private":
            return await self._send_private_message(message)
        
        # 广播模式
        elif message.message_type == "broadcast":
            return await self._send_broadcast_message(message)
        
        # 会议模式
        elif message.message_type == "meeting":
            return await self._send_meeting_message(message)
        
        return False
    
    async def _send_private_message(self, message: Message) -> bool:
        """发送私聊消息"""
        if message.recipient in self.agents:
            # 异步调用接收者的处理逻辑
            await self.agents[message.recipient].receive_message(message)
            return True
        else:
            print(f"通信中枢: 无法发送消息，接收者 {message.recipient} 未注册")
            return False
    
    async def _send_broadcast_message(self, message: Message) -> bool:
        """发送广播消息"""
        import asyncio
        tasks = []
        for agent_id, agent in self.agents.items():
            if agent_id != message.sender:  # 不发送给自己
                tasks.append(agent.receive_message(message))
        if tasks:
            await asyncio.gather(*tasks)
        return True
    
    async def _send_meeting_message(self, message: Message) -> bool:
        """发送会议消息"""
        import asyncio
        if message.meeting_id not in self.meetings:
            print(f"通信中枢: 无法发送会议消息，会议 {message.meeting_id} 不存在")
            return False
        
        meeting = self.meetings[message.meeting_id]
        meeting.add_message(message)
        
        # 向所有参会者发送消息
        tasks = []
        for participant in meeting.participants:
            if participant in self.agents and participant != message.sender:
                tasks.append(self.agents[participant].receive_message(message))
        if tasks:
            await asyncio.gather(*tasks)
        
        return True
    
    def create_meeting(self, organizer_id: str, topic: str, participants: List[str]) -> str:
        """创建会议"""
        meeting_id = f"meeting_{uuid.uuid4().hex[:8]}"
        meeting = MeetingRoom(meeting_id, topic, organizer_id)
        
        # 添加参与者
        for participant in participants:
            if participant in self.agents:
                meeting.add_participant(participant)
        
        self.meetings[meeting_id] = meeting
        print(f"通信中枢: 已创建会议 {meeting_id}，主题: {topic}，组织者: {organizer_id}")
        
        # 向所有参与者发送会议邀请
        invitation_message = Message(
            sender=organizer_id,
            recipient="all",
            subject=f"会议邀请: {topic}",
            content={
                "meeting_id": meeting_id,
                "topic": topic,
                "organizer": organizer_id,
                "participants": participants
            },
            message_type="meeting",
            meeting_id=meeting_id
        )
        
        self.send_message(invitation_message)
        return meeting_id
    
    def start_meeting(self, meeting_id: str) -> bool:
        """开始会议"""
        if meeting_id in self.meetings:
            self.meetings[meeting_id].start()
            print(f"通信中枢: 会议 {meeting_id} 已开始")
            return True
        return False
    
    def end_meeting(self, meeting_id: str) -> bool:
        """结束会议"""
        if meeting_id in self.meetings:
            self.meetings[meeting_id].end()
            print(f"通信中枢: 会议 {meeting_id} 已结束")
            return True
        return False
    
    def get_meeting_summary(self, meeting_id: str) -> Optional[Dict]:
        """获取会议总结"""
        if meeting_id in self.meetings:
            return self.meetings[meeting_id].get_summary()
        return None
    
    def get_message_history(self, agent_id: str = None, limit: int = 50) -> List[Message]:
        """获取消息历史"""
        if agent_id:
            # 获取与特定Agent相关的消息
            relevant_messages = []
            for msg in self.message_history:
                if msg.sender == agent_id or msg.recipient == agent_id or msg.recipient == "all":
                    relevant_messages.append(msg)
            return relevant_messages[-limit:]
        else:
            # 获取所有消息
            return self.message_history[-limit:]
    
    def get_online_agents(self) -> List[Dict[str, str]]:
        """获取在线Agent列表"""
        return [
            {
                "agent_id": agent_id,
                "name": agent.name,
                "agent_type": agent.agent_type
            }
            for agent_id, agent in self.agents.items()
        ]
