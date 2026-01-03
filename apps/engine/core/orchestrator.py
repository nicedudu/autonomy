import re
import json
from typing import AsyncGenerator, Dict, List, Any
from core.communication_bus import CommunicationBus
from core.registry.manager import discovery_service
from core.runtime.executor import AgentRuntime
from core.schema.models import CollaborationCall, Status

class Orchestrator:
    """
    中央任务编排中心。
    负责在不同 Agent 运行时之间流转执行权并维护全局状态。
    """

    def __init__(self):
        # 启动时执行资源发现
        discovery_service.initialize()
        self.runtimes: Dict[str, AgentRuntime] = {}
        self.bus = CommunicationBus()

    def _get_runtime(self, agent_id: str) -> AgentRuntime:
        if agent_id not in self.runtimes:
            manifest = discovery_service.agents.get(agent_id)
            if not manifest:
                raise ValueError(f"Agent {agent_id} not found in registry")
            self.runtimes[agent_id] = AgentRuntime(manifest)
        return self.runtimes[agent_id]

    async def dispatch(self, entry_agent_id: str, objective: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        分发初始目标并启动协作循环。
        """
        current_agent_id = entry_agent_id
        current_input = objective
        max_hops = 10
        hops = 0
        
        # 组织层级的全局共识
        global_facts: List[str] = []

        while hops < max_hops:
            hops += 1
            runtime = self._get_runtime(current_agent_id)
            
            # 更新运行时的系统上下文（包含组织名录与全局事实）
            team_roster = "\n".join([f"- @{m.name} ({m.agent_id}): {m.role}" for m in discovery_service.agents.all().values()])
            runtime.system_prompt = runtime.system_prompt.replace("{{team_roster}}", team_roster)
            
            if global_facts:
                runtime.system_prompt += f"\n\n[ORGANIZATION_FACTS]\n" + "\n".join(global_facts[-5:])

            # 执行当前 Agent 节点
            last_response = ""
            async for chunk in runtime.execute_async(current_input):
                if chunk["type"] == "stream":
                    last_response += chunk["content"]
                yield chunk

            # 协作调用解析 (RPC)
            call_match = re.search(r"<call>(.*?)<\/call>", last_response, re.DOTALL)
            if call_match:
                try:
                    call_data = json.loads(call_match.group(1).strip())
                    call = CollaborationCall(**call_data)
                    
                    print(f"[Orchestrator] Delegation: {current_agent_id} -> {call.target_id}")
                    
                    # 记录产出作为事实
                    global_facts.append(f"{runtime.name} delegated to {call.target_id} with task: {call.task}")
                    
                    current_agent_id = call.target_id
                    current_input = f"Task Assignment from {runtime.name}: {call.task}\nContext: {json.dumps(call.context, ensure_ascii=False)}"
                    continue
                except Exception as e:
                    yield {"type": "error", "content": f"Collaboration Protocol Error: {str(e)}"}
                    break

            # 如果不是入口 Agent 完成任务，则自动交还给主控（目前假设 entry_agent_id 是 coordinator）
            if current_agent_id != entry_agent_id:
                global_facts.append(f"{runtime.name} completed their segment.")
                current_input = f"Expert {runtime.name} feedback: {last_response}"
                current_agent_id = entry_agent_id
                continue

            break