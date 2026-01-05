from tools.web_search import web_search
from tools.web_fetch import web_fetch
from tools.planning import planning
from tools.researcher import researcher

# 核心工具原始列表 (被 @tool 装饰的函数)
CORE_TOOLS_RAW = [
    web_search,
    web_fetch,
    planning,
    researcher
]

# 标准化提取 BaseTool 对象
# 我们通过 __tool__ 属性获取装饰器注入的元数据封装
CORE_TOOLS = []
for item in CORE_TOOLS_RAW:
    if hasattr(item, "__tool__"):
        CORE_TOOLS.append(item.__tool__)
    else:
        # 兼容性处理
        CORE_TOOLS.append(item)

def get_core_tool_schemas():
    """动态生成所有工具的 OpenAI 标准 JSON Schema。"""
    return [t.to_schema() for t in CORE_TOOLS]