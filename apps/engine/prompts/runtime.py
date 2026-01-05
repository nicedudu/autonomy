from typing import Any

def get_observation_success_prompt(tool_name: str, output: Any) -> str:
    """提供工具执行成功的观测反馈。"""
    return f"\n[观测结果 - 成功]\n工具 '{tool_name}' 执行完毕。\n输出摘要: {str(output)[:5000]}"

def get_observation_failed_prompt(tool_name: str, error: str) -> str:
    """提供工具执行失败的观测反馈。"""
    return f"\n[观测结果 - 失败]\n错误详情: {error}\n指令: 请尝试根据错误信息进行自我修复或如实向用户报告。"

def get_max_turns_reached_prompt() -> str:
    """当达到推理轮次上限时的系统提示词。"""
    return "\n\n⚠️ 已达到系统预设的推理轮次上限。请基于当前已掌握的所有零碎信息，为用户做一次最终的总结报告。"

def get_final_summary_instruction() -> str:
    """引导模型进行最终总结的指令。"""
    return "请梳理目前所有的执行结果与观测事实，为用户合成一份结构严谨、逻辑清晰的最终答复。"