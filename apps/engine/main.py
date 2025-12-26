#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from agents.cpo_agent import CPOAgent

load_dotenv()

def main():
    print("=== Autonomy 多轮对话测试 ===")
    
    alice = CPOAgent(agent_id="cpo_agent", name="Alice")

    # 第一轮：启动任务 (使用 User Prompt 模板)
    print("\n[第一轮] 使用模板启动任务...")
    first_response = alice.run({
        "product_name": "智能人体工学椅",
        "market_region": "北美",
        "report_summary": "长期办公人群增加，护脊需求旺盛。"
    })
    print(f"Alice: {first_response}")

    # 第二轮：直接追问 (不再使用模板，仅发送原始输入)
    print("\n" + "-"*30)
    print("[第二轮] 直接追问 (Context 保持测试)...")
    follow_up = "针对你刚才提到的竞争风险，能再具体说说具体的头部厂商吗？"
    print(f"问: {follow_up}")
    
    second_response = alice.chat(follow_up)
    print(f"Alice: {second_response}")

if __name__ == "__main__":
    main()
