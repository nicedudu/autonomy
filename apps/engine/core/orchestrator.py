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
    负责多智能体协作调度、全局事实同步以及跨节点执行权的生命周期管理。
    """

    def __init__(self):
        """初始化编排器，挂载服务发现与通信总线。"""
        discovery_service.initialize()
        self.runtimes: Dict[str, AgentRuntime] = {}
        self.bus = CommunicationBus()

    def _get_runtime(self, agent_id: str) -> AgentRuntime:
        """
        获取或创建指定智能体的运行时实例。
        实现懒加载机制，仅在需要时初始化具体节点的运行环境。
        """
        if agent_id not in self.runtimes:
            manifest = discovery_service.agents.get(agent_id)
            if not manifest:
                raise ValueError(f"智能体注册表未找到 ID: {agent_id}")
            self.runtimes[agent_id] = AgentRuntime(manifest)
        return self.runtimes[agent_id]

    async def dispatch(self, entry_agent_id: str, objective: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        分发任务目标并启动自主编排循环。
        
        Args:
            entry_agent_id: 入口智能体 ID（通常为主控节点）。
            objective: 用户提出的宏观目标。
            
        Yields:
            包含执行过程（流式文本、状态更新、错误信息）的字典序列。
        """
        current_agent_id = entry_agent_id
        current_input = objective
        max_hops = 12 # 防止协作无限回环
        hops = 0
        global_facts: List[str] = [] # 存储跨节点的共识事实

        try:
            while hops < max_hops:
                hops += 1
                runtime = self._get_runtime(current_agent_id)
                
                # 构建动态团队名录，注入最新的节点状态
                all_agents = discovery_service.agents.all().values()
                team_roster = "团队名录:\n" + "\n".join([f"- @{m.name} ({m.agent_id}): {m.role}" for m in all_agents])

                print(f"[Orchestrator] 调度激活 -> {runtime.name} ({current_agent_id})")

                # 判定当前是否为入口节点（负责与用户直接对话）
                is_entry_agent = current_agent_id == entry_agent_id
                
                last_response = ""
                async for chunk in runtime.execute_async(
                    current_input, 
                    team_roster=team_roster, 
                    global_facts=global_facts
                ):
                    # 注意：runtime.execute_async 内部已经包含了 print(chunk) 逻辑
                    if chunk["type"] == "stream":
                        content = chunk["content"]
                        last_response += content
                        
                        # 仅对前端推送逻辑进行过滤，控制台打印由 executor.py 内部处理
                        if is_entry_agent:
                            yield chunk
                        else:
                            # 专家节点运行时，仅透传状态标签以保持前端进度感
                            if "<status>" in content or "<plan>" in content:
                                yield chunk
                    else:
                        yield chunk

                # 解析跨节点协作请求
                call_match = re.search(r"<call>(.*?)<\/call>", last_response, re.DOTALL)
                if call_match:
                    try:
                        call_data = json.loads(call_match.group(1).strip())
                        call = CollaborationCall(**call_data)
                        global_facts.append(f"由 {runtime.name} 委派给 {call.target_id}，任务: {call.task}")
                        
                        # 切换执行上下文至目标专家节点
                        current_agent_id = call.target_id
                        current_input = f"指派自 {runtime.name}: {call.task}\n上下文: {json.dumps(call.context, ensure_ascii=False)}"
                        continue
                    except Exception as e:
                        yield {"type": "error", "content": f"协作协议解析失败: {str(e)}"}
                        break

                # 处理专家节点任务完成后的回滚逻辑
                if current_agent_id != entry_agent_id:
                    global_facts.append(f"节点 {runtime.name} 已完成阶段性任务。")
                    current_input = f"反馈通知：专家节点 {runtime.name} ({current_agent_id}) 已完成分配的任务。\n产出如下：\n{last_response}"
                    current_agent_id = entry_agent_id
                    continue

                # 主控节点完成任务，退出循环
                break
        except Exception as e:
            # 捕获异常并转化为标准错误消息推送到前端
            error_msg = f"系统运行时发生致命异常: {type(e).__name__} - {str(e)}"
            print(f"\n[CRITICAL FAILURE] {error_msg}")
            yield {"type": "error", "content": error_msg}