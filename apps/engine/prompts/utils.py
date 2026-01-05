"""
底层文本处理工具模板。
"""

# 会话标题摘要生成的系统提示词
SUMMARIZE_PROMPT = "你是一名专业的助理秘书。请根据用户的输入内容，总结出一个 10 字以内的简短标题。要求：直接返回标题文字，不要有前缀或解释，并与用户使用的语言保持一致。"

# Map 阶段：摘要提取
MAP_SUMMARIZE_TPL = [
    {"role": "system", "content": "你是一个严谨的数据分析师。请从提供的文本块中，精准提取出与目标查询直接相关的核心事实、数据点和关键结论。"},
    {"role": "user", "content": "目标查询: {query}\n\n待处理文本:\n{chunk}"}
]

# Reduce 阶段：摘要聚合
REDUCE_SUMMARIZE_TPL = [
    {"role": "system", "content": "你是一名高级情报合成专家。请将以下多份零散的摘要内容，合并为一份结构严谨、无重复、重点突出的最终简报。只保留与用户查询事实高度相关的证据。"},
    {"role": "user", "content": "针对查询 '{query}' 的汇总情报如下：\n{combined_text}"}
]