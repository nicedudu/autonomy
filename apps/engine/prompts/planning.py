"""
任务规划协议提示词。
"""

PLANNING_PROTOCOL = """[动态规划协议 - PLANNING PROTOCOL]
对于复杂任务，你必须在 <plan> 标签中维护一个结构化的 JSON 数组，并使用 ```json 代码块包裹：
<plan>
```json
[
  {"step": "步骤描述内容", "status": "not_started | in_progress | completed | blocked"}
]
```
</plan>

[准则]
1. 颗粒度：每个步骤必须是可验证的原子操作。
2. 动态调整：每轮执行后，根据工具的反馈实时更新数组中对应步骤的状态。
3. 退出逻辑：当所有必要步骤均标记为 "completed" 时，应立即转向合成最终答复。
4. 终结协议：当你准备给出最终答案时，必须在回复中包含全量标记为 "completed" 的计划块。"""
