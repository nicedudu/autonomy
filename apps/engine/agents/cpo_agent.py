from typing import List, Dict, Any
import time
from agents.base_agent import BaseAgent, ToolCall
from core.reasoning_engine import ReActReasoningEngine

from agents.base_agent import BaseAgent, ToolCall, Message

class CPOAgent(BaseAgent):
    """首席选品官Agent"""
    
    def __init__(self, agent_id: str, name: str):
        # ... (保持现有初始化逻辑)
        tools = [
            "Trend_Hunter",
            "Market_Scraper",
            "Vision_Analyst",
            "Profit_Calculator",
            "SCM_Bridge"
        ]
        
        super().__init__(agent_id=agent_id, agent_type="cpo", name=name, tools=tools)
        
        # 初始化ReAct思考引擎
        self.reasoning_engine = ReActReasoningEngine()
        
        # CPO Agent的特定属性
        self.current_task = None
        self.thought_process = []
        self.product_selection_history = []
    
    def _handle_product_analysis_request(self, content: Dict[str, Any]):
        """处理产品分析请求"""
        product = content.get("product")
        print(f"[{self.name}] 正在利用高阶 LLM 生成产品 {product} 的战略前瞻...")
        
        # 利用 PromptManager 渲染 Prompt
        strategy_prompt = self.prompt_manager.render_prompt(
            agent_type="cpo", 
            prompt_key="strategic_insight", 
            product_name=product,
            market_region="Global" # 这里可以从 content 中获取
        )
        
        insight = self.ask_llm(strategy_prompt)
        print(f"[{self.name}] 战略见解: {insight}")

        # 执行原有的 ReAct 逻辑
        task = f"分析产品 {product} 的市场潜力"
        # ... (后续逻辑保持不变)
        plan = self.plan(task)
        
        # 开始执行第一步
        context = {"product": product, "insight": insight}
        tool_calls = self.think(task, context)
        
        # 执行工具调用
        results = self.act(tool_calls)
        self.observe(results)
    
    def _handle_product_approval(self, content: Dict[str, Any]):
        """处理选品批准"""
        product_id = content.get("product_id")
        print(f"[{self.name}] 选品批准: {product_id}")
        
        # 记录批准结果
        self.product_selection_history.append({
            "product_id": product_id,
            "status": "approved",
            "timestamp": time.time(),
            "details": content
        })
        
        # 向供应链部门发送通知
        self.send_message(
            recipient="scm_agent",
            subject="product_selection_approved",
            content={"product_id": product_id}
        )
    
    def _handle_product_rejection(self, content: Dict[str, Any]):
        """处理选品拒绝"""
        product_id = content.get("product_id")
        reason = content.get("reason")
        print(f"[{self.name}] 选品拒绝: {product_id}，原因: {reason}")
        
        # 记录拒绝结果
        self.product_selection_history.append({
            "product_id": product_id,
            "status": "rejected",
            "timestamp": time.time(),
            "details": content
        })
    
    def get_thought_process_summary(self) -> Dict[str, Any]:
        """获取思考过程摘要"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "current_task": self.current_task,
            "thought_process": [
                {
                    "step": tp.step,
                    "step_name": tp.step_name,
                    "thought": tp.thought,
                    "confidence": tp.confidence,
                    "tool_calls": [
                        {
                            "tool_name": tc.tool_name,
                            "parameters": tc.parameters,
                            "thought": tc.thought
                        } for tc in tp.tool_calls
                    ] if tp.tool_calls else [],
                    "observation": tp.observation
                } for tp in self.thought_process
            ]
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取CPO Agent的绩效指标"""
        # 计算绩效指标
        approved_products = [p for p in self.product_selection_history if p["status"] == "approved"]
        rejected_products = [p for p in self.product_selection_history if p["status"] == "rejected"]
        
        return {
            "total_product_analyses": len(self.product_selection_history),
            "approved_products": len(approved_products),
            "rejected_products": len(rejected_products),
            "approval_rate": len(approved_products) / len(self.product_selection_history) * 100 if self.product_selection_history else 0,
            "avg_decision_time": 0,  # 待实现
            "successful_products": 0  # 待实现
        }
