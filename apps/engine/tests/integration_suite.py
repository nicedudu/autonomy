"""
集成测试套件 (Integration Test Suite) - 参数化版本

职责：支持运行全量测试或通过 --index 指定运行单个场景。
"""

import asyncio
import uuid
import os
import argparse
from typing import List, Dict, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from core.agent.agent import Agent
from core.agent.profile import AgentProfile
from core.agent.executor import AgentExecutor
from core.session.session import Session
from core.agent.registry import agent_registry

# 显式激活工具注册
import tools 

class IntegrationTester:
    def __init__(self):
        self.executor = AgentExecutor()

    async def run_scenario(self, scenario: Dict[str, str], profile_id: str = "primary_agent"):
        name = scenario["name"]
        user_input = scenario["input"]
        
        print(f"\n\033[95m{'='*20} 正在执行场景: {name} {'='*20}\033[0m")
        print(f"用户输入: {user_input}\n")

        profile = agent_registry.get_profile(profile_id)
        if not profile:
            print(f"\033[31m错误: 找不到 Profile {profile_id}\033[0m")
            return

        session = Session.create_root(user_id="test_runner")
        agent = Agent(profile=profile, session=session)

        try:
            async for event in self.executor.run(agent, input_text=user_input):
                etype = event.get("type")
                content = event.get("content", "")

                if etype == "observation":
                    print(f"\033[32m[OBSERVATION]\033[0m 来自 {event.get('source')}: {content[:200]}...")
                elif etype == "conclusion":
                    print(f"\033[92m[CONCLUSION]\033[0m {content}")
                elif etype == "error":
                    print(f"\033[31m[ERROR]\033[0m {content}")
                elif etype == "status":
                    print(f"\033[33m[STATUS]\033[0m {content}")

        except Exception as e:
            print(f"\033[31m执行过程中发生未捕获异常: {str(e)}\033[0m")

SCENARIOS = [
    {"name": "L1_Basic_Greeting", "input": "你好，请介绍一下你自己和你现在的运行环境。"},
    {"name": "L2_Workspace_Discovery", "input": "查看当前目录下有哪些文件。"},
    {"name": "L3_Parallel_Search", "input": "请帮我搜索一下 DeepSeek 的最新动态，并同步搜索 OpenAI 的最新动态。"},
    {"name": "L4_Sequential_DAG", "input": "请读取 README.md 文件的内容，然后将其翻译成英文并输出。"},
    {"name": "L5_Recursive_Audit", "input": "请对当前工程的架构进行深度审计，并给我一份关于代码健壮性的改进建议报告。"},
    {"name": "L6_Memory_Pressure", "input": "让我们开始一连串的数学计算。第一步：1+1等于几？"}
]

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=int, help="要运行的测试场景索引 (0-5)")
    args = parser.parse_args()

    tester = IntegrationTester()

    if args.index is not None:
        if 0 <= args.index < len(SCENARIOS):
            await tester.run_scenario(SCENARIOS[args.index])
        else:
            print(f"索引超出范围。有效范围: 0-{len(SCENARIOS)-1}")
    else:
        # 默认运行所有 (用于兼容旧调用)
        for s in SCENARIOS:
            await tester.run_scenario(s)
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
