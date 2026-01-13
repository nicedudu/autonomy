# Autonomy 工具开发指南 (V2.0 - 自举模式)

## 1. 设计哲学
为了降低 Agent 工具的维护成本，我们引入了**“自举式工具定义”**。开发者只需编写标准的 Python 函数，并通过 `@tool` 装饰器进行标注，系统会自动解析函数签名、类型提示和 Docstring，生成符合 OpenAI/MCP 标准的 JSON Schema。

## 2. 核心特性
- **零配置**：无需手动编写复杂的 JSON Schema。
- **强类型检查**：利用 Python Type Hints 实现运行时的参数校验。
- **自动化文档**：Docstring 自动转化为 Agent 可理解的工具描述。
- **上下文感知**：支持自动注入 `session_id` 等运行时上下文。

## 3. 快速开始

### 3.1 定义一个基础工具
使用 `@tool` 装饰器标记函数。

```python
from core.tools.registry import tool

@tool
async def get_weather(location: str, unit: str = "celsius"):
    """
    获取指定城市的实时天气情况。
    
    Args:
        location: 城市名称 (例如: "Shanghai")
        unit: 温度单位，可选 "celsius" 或 "fahrenheit"
    """
    # 实现逻辑
    return {"temp": 25, "unit": unit, "condition": "Sunny"}
```

### 3.2 自动注入上下文
如果函数参数中包含 `session_id` 或 `user_context`，系统会在调用时自动注入。

```python
@tool
async def save_memory(content: str, session_id: str):
    """
    将重要信息存入长期记忆。
    """
    # session_id 会由 Runtime 自动注入，模型不可见
    pass
```

## 4. 自举原理 (Internal Mechanism)

系统通过以下步骤实现自举：
1. **内省 (Introspection)**：使用 `inspect` 库读取函数的 `signature`。
2. **Schema 生成**：利用 `pydantic.create_model` 动态创建一个输入验证模型，并导出 `model_json_schema()`。
3. **Docstring 解析**：解析 Google 风格或 NumPy 风格的 Docstring，提取参数描述。
4. **注册**：将包装后的函数对象存入 `ToolRegistry`。

## 5. 最佳实践
- **清晰的描述**：Agent 依赖 Docstring 来理解工具，请务必编写清晰、简洁的函数描述。
- **显式类型**：尽量避免使用 `Any`，使用具体的类型（如 `List[str]`, `Optional[int]`）有助于生成更精准的 Schema。
- **纯净的返回值**：工具应返回可被 JSON 序列化的对象。
