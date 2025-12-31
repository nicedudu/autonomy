import re
from typing import Dict, Any, Optional, AsyncGenerator
from core.communication_bus import CommunicationBus
from core.agent_manager import agent_manager
from agents.base_agent import CollaborationCall

class Orchestrator:
    """
    Autonomy 生产级调度引擎 (Nexus V4)
    基于 AgentManager 实现动态发现与状态感知的调度循环。
    """
    
    def __init__(self):
        self.bus = CommunicationBus()
        # 启动时自动发现注册表
        agent_manager.discover_registry()

    async def run_autonomous_loop(self, agent_id: str, content: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        [Nexus V4] 增强型自主编排循环。
        支持智能体间的状态快照传递与动态能力发现。
        """
        # 1. 初始化组织成员名录 (从注册中心发现)
        manifests = agent_manager.get_all_manifests()
        team_roster = "\n".join([
            f"- @{m.name} ({m.agent_id}): {m.role}"
            for m in manifests
        ])

        current_agent_id = agent_id
        current_input = content
        max_depth = 8 
        depth = 0
        
        global_context_facts = []

        while depth < max_depth:
            depth += 1
            # 从 AgentManager 动态获取/激活智能体
            agent = agent_manager.get_agent(current_agent_id)
            if not agent:
                yield {"type": "error", "content": f"无法激活智能体: {current_agent_id}"}
                break

            # 确保 Agent 接入总线
            if not agent.communication_bus:
                agent.set_communication_bus(self.bus)

            print(f"\n[Orchestrator] 调度流激活 -> {agent.name} ({current_agent_id})")

            # 动态注入全局事实到 Agent 系统提示词
            original_sys_prompt = agent.system_prompt
            context_str = "\n".join(global_context_facts[-5:]) # 传递最近 5 条事实
            updated_sys_prompt = original_sys_prompt.replace("{{team_roster}}", team_roster)
            if context_str:
                updated_sys_prompt += f"\n\n[组织已达成共识的事实]:\n{context_str}"
            
            agent.system_prompt = updated_sys_prompt

            # 执行当前 Agent
            accumulated_response = ""
            async for chunk in agent.chat_stream_async(current_input):
                accumulated_response += chunk
                yield {"type": "stream", "agent_id": current_agent_id, "content": chunk}

            # 恢复原始提示词
            agent.system_prompt = original_sys_prompt

            # 2. 严格 RPC 解析逻辑 (Nexus V4 Production Standard)
            call_match = re.search(r"<call>(.*?)<\/call>", accumulated_response, re.DOTALL)
            if call_match:
                call_raw = call_match.group(1).strip()
                
                try:
                    import json
                    call_data = json.loads(call_raw)
                    # 强制校验字段完整性
                    call_obj = CollaborationCall(**call_data)
                    target_agent_id = call_obj.target_id
                    task_instruction = call_obj.task
                    
                    # 检查目标是否存在
                    target_agent = agent_manager.get_agent(target_agent_id)
                    if not target_agent:
                        yield {"type": "error", "content": f"RPC 调用失败：目标智能体 {target_agent_id} 不存在。"}
                        break

                    # 校验接口契约 (Interface Validation)
                    # 如果目标定义了 input_schema，则应进行校验 (此处留出 Hook 供后续细化)
                    print(f"[Orchestrator] 协议校验通过: {current_agent_id} -> {target_agent_id}")
                    
                except json.JSONDecodeError:
                    yield {"type": "error", "content": f"协议格式错误：<call> 内必须是合法的 JSON。接收到: {call_raw[:50]}..."}
                    break
                except Exception as e:
                    yield {"type": "error", "content": f"协议校验失败：{str(e)}"}
                    break
                
                # 记录全局事实并切换上下文
                conclusion_snippet = accumulated_response[:200].replace("<thought>", "").replace("</thought>", "").strip()
                global_context_facts.append(f"{agent.name} 结论: {conclusion_snippet}...")
                
                current_agent_id = target_agent_id
                current_input = task_instruction
                continue 
            
            # 3. 归还执行权逻辑
            if current_agent_id != "ceo_agent":
                print(f"[Orchestrator] {current_agent_id} 工作闭环，返回主控")
                # 将该专家的产出作为事实
                global_context_facts.append(f"专家 {agent.name} 已完成其负责的环节，结果已产出。")
                current_input = f"专家 {agent.name} ({current_agent_id}) 已完成任务，其反馈如下：\n{accumulated_response}\n请进行下一步决策。"
                current_agent_id = "ceo_agent"
                continue
            
            # 4. 真正结束
            break
            
            
            
            