def get_map_summarize_prompt(query: str, chunk: str) -> list:
    """提供 Map 阶段的摘要提取提示词（全中文）。"""
    return [
        {"role": "system", "content": "你是一个严谨的数据分析师。请从提供的文本块中，精准提取出与目标查询直接相关的核心事实、数据点和关键结论。"},
        {"role": "user", "content": f"目标查询: {query}\n\n待处理文本:\n{chunk}"}
    ]

def get_reduce_summarize_prompt(query: str, combined_text: str) -> list:
    """提供 Reduce 阶段的摘要聚合提示词（全中文）。"""
    return [
        {"role": "system", "content": "你是一名高级情报合成专家。请将以下多份零散的摘要内容，合并为一份结构严谨、无重复、重点突出的最终简报。只保留与用户查询事实高度相关的证据。"},
        {"role": "user", "content": f"针对查询 '{query}' 的汇总情报如下：\n{combined_text}"}
    ]