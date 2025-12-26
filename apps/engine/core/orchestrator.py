from typing import Dict, List, Any, Optional
import time
import uuid
from core.communication_bus import CommunicationBus
from agents.base_agent import BaseAgent, Message

class Orchestrator:
    """
    Autonomy 中央编排器 (CEO 的技术实现层)
    负责 Agent 注册、生命周期管理、以及跨部门协作的调度。
    """
    
    def __init__(self):
        self.bus = CommunicationBus()
        self.agents: Dict[str, BaseAgent] = {}
        self.active_tasks = {} # 追踪进行中的全局任务
        self.running = False

    def register_agent(self, agent: BaseAgent):
        """将 Agent 接入 Nexus 网络"""
        agent.set_communication_bus(self.bus)
        self.agents[agent.agent_id] = agent
        self.bus.register_agent(agent)
        print(f"[Orchestrator] 部门已就绪: {agent.name} ({agent.agent_type})")

    def create_global_task(self, description: str, initiator_id: str):
        """创建一个跨部门的全局任务"""
        task_id = f"task_{uuid.uuid4().hex[:6]}"
        self.active_tasks[task_id] = {
            "description": description,
            "status": "pending",
            "start_time": time.time(),
            "history": []
        }
        
        # 广播新任务通知
        self.bus.send_message(Message(
            sender="orchestrator",
            recipient="all",
            subject="new_global_task",
            content={"task_id": task_id, "description": description},
            message_type="broadcast"
        ))
        return task_id

    def start_event_loop(self, iterations: int = 10):
        """
        启动中央事件循环。
        在自研框架中，我们通过控制循环来观察和干预 Agent 的交互。
        """
        print("\n=== Autonomy 运营中中心启动 ===")
        self.running = True
        
        for i in range(iterations):
            if not self.running:
                break
                
            print(f"\n--- [周期 {i+1}] 正在处理跨部门协同 ---")
            
            # 1. 检查消息队列（在 CommunicationBus 中处理）
            # 2. 如果存在挂起的任务需要人工审批，可以在这里拦截
            self._check_for_human_intervention()
            
            # 模拟时间流逝，让 Agent 有时间“思考”
            time.sleep(1)
        
        print("\n=== 周期结束，系统进入待机模式 ===")

    def _check_for_human_intervention(self):
        """
        人类审批拦截点。
        如果检测到涉及财务支出或高风险策略的消息，在此挂起。
        """
        # 示例：检查是否有采购单等待审批
        messages = self.bus.get_message_history(limit=5)
        for msg in messages:
            if msg.subject == "procurement_plan_ready":
                print(f"⚠️  [审批提醒] 检测到来自 SCM 的采购计划：{msg.content.get('product_id')}")
                print(f"💰  预估金额：${msg.content.get('estimated_cost')}.\n")
                # 在真实应用中，这里会通过 WebSocket 推送到手机端
                # 这里我们模拟自动批准
                print("✅  [系统自动审批] 符合预算策略。")

    def shutdown(self):
        self.running = False
        print("[Orchestrator] 正在安全关闭 Nexus 节点...")
