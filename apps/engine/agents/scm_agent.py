from typing import List, Dict, Any, Optional
import time
import json
from agents.base_agent import BaseAgent, ToolCall, Message
from core.reasoning_engine import ReActReasoningEngine

class SCMAgent(BaseAgent):
    """
    供应链官 Agent (SCM)
    专注于：成本核算、供应商开发、库存管理。
    使用的模型通常为性价比高的 gpt-4o-mini。
    """
    
    def __init__(self, agent_id: str, name: str):
        tools = ["SCM_Bridge", "Profit_Calculator"]
        super().__init__(agent_id=agent_id, agent_type="scm", name=name, tools=tools)
        
        self.reasoning_engine = ReActReasoningEngine()
        self.active_procurements = {} # 记录进行中的采购任务

    async def process_message(self, message: Message):
        """处理部门间消息"""
        sender = message.sender
        subject = message.subject
        content = message.content
        
        print(f"[{self.name}] 接收到来自 {sender} 的指令: {subject}")
        
        if subject == "product_selection_approved":
            # CPO 选品获批，触发供应链准备
            product_id = content.get("product_id")
            # 注意：如果这些方法涉及耗时 LLM 调用，也应该改为 async
            self._handle_new_product_pipeline(product_id)
        
        elif subject == "request_cost_analysis":
            # 响应财务或CEO的成本分析请求
            self._handle_cost_analysis(content)
            
        elif subject == "task_delegation":
            instruction = content.get("instruction")
            print(f"[{self.name}] 正在执行来自 CEO 的任务: {instruction[:50]}...")
            
            # 使用流式回复到总线
            await self.chat_to_bus(
                user_input=f"这是来自 CEO 的指令，请执行并给出专业分析：\n{instruction}",
                recipient=sender
            )

    def _handle_new_product_pipeline(self, product_id: str):
        """处理新产品上架前的供应链管道"""
        print(f"[{self.name}] 正在为产品 {product_id} 建立供应链管道...")
        
        # 使用 PromptManager 渲染 Prompt
        strategy_prompt = self.prompt_manager.render_prompt(
            agent_type="scm",
            prompt_key="pipeline_strategy",
            product_name=product_id,
            target_market="US",
            initial_quantity="500"
        )
        
        thought_summary = self.ask_llm(strategy_prompt)
        print(f"[{self.name}] 供应链策略建议: {thought_summary}")

        # 调用工具：查询供应商和初步报价
        task = f"获取产品 {product_id} 的供应商报价和交期"
        # 这里模拟 ReAct 的一步
        tool_call = ToolCall(
            tool_name="SCM_Bridge",
            parameters={"action": "request_cost_quote", "products": [product_id]},
            thought="需要实时报价数据以完成供应链评估"
        )
        
        results = self.act([tool_call])
        self.observe(results)
        
        # 广播结果
        if results[0].success:
            self.broadcast_message(
                subject="scm_pipeline_initialized",
                content={
                    "product_id": product_id,
                    "scm_status": "ready",
                    "strategy": thought_summary,
                    "quote_data": results[0].result
                }
            )

    def _handle_cost_analysis(self, content: Dict[str, Any]):
        """处理成本分析请求"""
        # 具体的分析逻辑...
        pass

    def think(self, task: str, context: Dict[str, Any] = None) -> List[ToolCall]:
        # 兼容基类的抽象方法
        return self.reasoning_engine.think(task, context)

    def plan(self, task: str) -> List[Dict[str, Any]]:
        return [
            {"step": 1, "name": "询价", "tools": ["SCM_Bridge"]},
            {"step": 2, "name": "成本核算", "tools": ["Profit_Calculator"]}
        ]
