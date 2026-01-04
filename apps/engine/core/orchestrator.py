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
    管理多智能体协作、全局事实记录以及跨节点的执行权调度。
    """

    def __init__(self):
        """初始化编排器，自动加载资源清单。"""
        discovery_service.initialize()
        self.runtimes: Dict[str, AgentRuntime] = {}
        self.bus = CommunicationBus()

    def _get_runtime(self, agent_id: str) -> AgentRuntime:
        """获取或创建指定智能体的运行时实例（惰性加载）。"""
        if agent_id not in self.runtimes:
            manifest = discovery_service.agents.get(agent_id)
            if not manifest:
                raise ValueError(f"智能体注册表未找到 ID: {agent_id}")
            self.runtimes[agent_id] = AgentRuntime(manifest)
        return self.runtimes[agent_id]

    async def dispatch(self, entry_agent_id: str, objective: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        分发初始目标并启动自主编排循环。
        """
        current_agent_id = entry_agent_id
        current_input = objective
        max_hops = 12
        hops = 0
        global_facts: List[str] = []

        try:
            while hops < max_hops:
                hops += 1
                runtime = self._get_runtime(current_agent_id)
                
                all_agents = discovery_service.agents.all().values()
                team_roster = "团队名录:\n" + "\n".join([f"- @{m.name} ({m.agent_id}): {m.role}" for m in all_agents])

                print(f"[Orchestrator] 调度激活 -> {runtime.name} ({current_agent_id})")

                last_response = ""
                async for chunk in runtime.execute_async(
                    current_input, 
                    team_roster=team_roster, 
                    global_facts=global_facts
                ):
                    if chunk["type"] == "stream":
                        last_response += chunk["content"]
                    yield chunk

                call_match = re.search(r"<call>(.*?)<\/call>", last_response, re.DOTALL)
                if call_match:
                    try:
                        call_data = json.loads(call_match.group(1).strip())
                        call = CollaborationCall(**call_data)
                        global_facts.append(f"由 {runtime.name} 委派给 {call.target_id}，任务: {call.task}")
                        
                        current_agent_id = call.target_id
                        current_input = f"指派自 {runtime.name}: {call.task}\n上下文: {json.dumps(call.context, ensure_ascii=False)}"
                        continue
                    except Exception as e:
                        yield {"type": "error", "content": f"协作协议解析失败: {str(e)}"}
                        break

                if current_agent_id != entry_agent_id:
                    global_facts.append(f"节点 {runtime.name} 已完成阶段性任务。")
                    current_input = f"反馈通知：专家节点 {runtime.name} ({current_agent_id}) 已完成分配的任务。\n产出如下：\n{last_response}"
                    current_agent_id = entry_agent_id
                    continue

                break
        except Exception as e:
            # 捕获所有导致循环崩溃的异常，并推送到前端
            error_msg = f"系统运行时发生致命异常: {type(e).__name__} - {str(e)}"
            print(f"\n[CRITICAL FAILURE] {error_msg}")
            yield {"type": "error", "content": error_msg}
