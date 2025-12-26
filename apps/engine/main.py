#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from jinja2 import Template
from agents.cpo_agent import CPOAgent

# 加载环境变量
load_dotenv()

def main():
    print("=== Autonomy 真实 API 测试 (MVP) ===")
    
    # 1. 初始化 CPO Agent Alice
    try:
        alice = CPOAgent(agent_id="cpo_agent", name="Alice")
        print(f"\n[系统] 已成功连接智能体: {alice.name} ({alice.agent_id})")
    except Exception as e:
        print(f"\n[错误] 初始化失败: {e}")
        return

    # 2. 检查配置
    config = alice.llm_factory.get_merged_config(alice.agent_id)
    print(f"[系统] 使用模型: {config.get('model')}")
    print(f"[系统] 供应商标准: {config.get('provider_type')}")

    # 3. 测试 1: 直接对话
    print("\n" + "="*20)
    print("测试 1: 直接对话 (问候)")
    print("="*20)
    
    question = "你好 Alice，作为首席选品官，请简单介绍一下你的核心能力。"
    
    print("\n>>> 最终合并发送的 Prompt (测试 1) <<<")
    print(f"[系统提示词]:\n{alice.system_prompt}")
    print(f"\n[用户指令]:\n{question}")
    print(">"*35 + "\n")
    
    response = alice.ask_llm(question)
    print(f"Alice 的回答:\n{response}")

    # 4. 测试 2: 用户提示词 (User Prompt) 渲染测试
    print("\n" + "="*20)
    print("测试 2: 用户提示词模板渲染测试")
    print("="*20)
    
    # 从配置中获取在后台保存的 user_prompt 模板
    template_str = config.get("user_prompt", "")
    if not template_str:
        print("[警告] 数据库中未找到用户提示词模板。\n")
    else:
        # 模拟渲染参数
        render_data = {
            "product_name": "智能降噪睡眠眼罩",
            "market_region": "欧洲",
            "report_summary": "当前睡眠经济呈现爆发式增长，消费者对穿戴式睡眠设备需求增加。"
        }
        
        try:
            rendered_task = Template(template_str).render(**render_data)
            
            print("\n>>> 最终合并发送的 Prompt (测试 2) <<<")
            print(f"[系统提示词]:\n{alice.system_prompt}")
            print(f"\n[用户指令 (已渲染)]:\n{rendered_task}")
            print(">"*35 + "\n")
            
            print("正在根据渲染后的指令进行分析...")
            task_response = alice.ask_llm(rendered_task)
            print(f"\n分析结果:\n{task_response}")
        except Exception as e:
            print(f"[错误] 渲染或调用失败: {e}")

    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()
