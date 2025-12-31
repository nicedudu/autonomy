import re
import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator
from agents.base_agent import BaseAgent

from core.communication_bus import CommunicationBus

class Orchestrator:
    """
    Autonomy 生产级调度引擎 (Nexus V3)
    实现了基于 <call> 标签的自主任务委派与循环执行逻辑。
    """
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.bus = CommunicationBus()

    def register_agent(self, agent: BaseAgent):
        """将 Agent 注册到调度中心并接入总线"""
        agent.set_communication_bus(self.bus)
        self.agents[agent.agent_id] = agent
        print(f"[Orchestrator] 智能体已注册并接入总线: {agent.name} ({agent.agent_id})")

    async def run_autonomous_loop(self, agent_id: str, content: str) -> AsyncGenerator[Dict[str, Any], None]:
        # 1. 构建动态成员名录 (仅列表项)
        team_roster = "\n".join([
            f"- @{a.name} ({aid}): {a.role if hasattr(a, 'role') else '专家'}"
            for aid, a in self.agents.items()
        ])

        current_agent_id = agent_id
        current_input = content
        max_depth = 5
        depth = 0

        while depth < max_depth:
            depth += 1
            agent = self.agents.get(current_agent_id)
            if not agent:
                yield {"type": "error", "content": f"找不到智能体: {current_agent_id}"}
                break

            # 动态更新 Agent 的系统提示词
            original_sys_prompt = agent.system_prompt
            # 替换占位符
            updated_sys_prompt = original_sys_prompt.replace("{{team_roster}}", team_roster)
            agent.system_prompt = updated_sys_prompt

            # 执行当前 Agent
            accumulated_response = ""
            async for chunk in agent.chat_stream_async(current_input):
                accumulated_response += chunk
                yield {"type": "stream", "agent_id": current_agent_id, "content": chunk}

            # 恢复原始提示词
            agent.system_prompt = original_sys_prompt

            # 2. 检查是否有 <call> 标签
            call_match = re.search(r"<call>(.*?)<\/call>", accumulated_response, re.DOTALL)
            if call_match:
                call_content = call_match.group(1).strip()
                
                # 解析目标 Agent，例如 "@Alice 任务描述"
                target_match = re.match(r"@(\w+)\s+(.*)", call_content, re.DOTALL)
                if target_match:
                    target_name = target_match.group(1)
                    task_instruction = target_match.group(2)
                    
                    # 通过名称或 ID 匹配 Agent
                    target_agent_id = self._find_agent_id_by_name(target_name)
                    if target_agent_id:
                        print(f"[Orchestrator] 检测到委派: {current_agent_id} -> {target_agent_id}")
                        current_agent_id = target_agent_id
                        current_input = task_instruction
                        continue # 进入下一轮循环，执行 Sub-agent
                    else:
                        yield {"type": "error", "content": f"无法委派：找不到名为 {target_name} 的智能体"}
                        break
                else:
                    yield {"type": "error", "content": "解析 <call> 格式失败，请确保格式为 @Name 指令"}
                    break
            
            # 3. 如果没有 <call>，检查是否需要归还给 CEO
            if current_agent_id != "ceo_agent":
                print(f"[Orchestrator] {current_agent_id} 任务结束，返回执行权给 CEO")
                current_input = f"专家 {current_agent_id} 已完成任务，其反馈如下：\n{accumulated_response}\n请进行下一步决策。"
                current_agent_id = "ceo_agent"
                continue
            
            # 4. 如果 CEO 也没有 <call> 了，则整个循环真正结束
            break

    def _find_agent_id_by_name(self, name: str) -> Optional[str]:
        """通过名称模糊匹配 Agent ID"""
        # 先尝试完全匹配 identifier
        if name in self.agents: return name
        # 再尝试匹配 .name 属性（不分大小写）
        for aid, agent in self.agents.items():
            if agent.name.lower() == name.lower():
                return aid
        # 匹配 cpo_agent, scm_agent 中的角色前缀
        for aid in self.agents:
            if aid.startswith(name.lower()):
                return aid
        return None