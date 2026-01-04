def get_toolcall_instruction() -> str:
    """
    提供 Autonomy 专用的工具调用协议指令。
    使用 JSON RPC 风格的结构化标签，以确保在各种模型上的鲁棒性。
    """
    return """[工具调用协议 - ACTION PROTOCOL]
当你决定使用工具时，必须使用以下严格的格式：
<action>
{
    "tool_name": "工具名称",
    "params": {
        "参数名": "参数值"
    }
}
</action>

[强制约束]
1. 每次响应仅限调用一个工具。
2. 严禁在 <action> 标签外添加任何解释性文字或代码块。
3. 所有的参数必须符合工具的 JSON Schema 定义。
4. 如果目标已达成，请使用 `terminate` (如果可用) 或直接输出最终结论，严禁继续调用工具。"""
