# Autonomy Engine V2.0 架构重构技术蓝图

## 1. 设计哲学 (Design Philosophies)

### 1.1. 灵魂与大脑的分离 (Soul-Brain Separation)
*   **Soul (逻辑核心)**：智能体的“性格”、执行 SOP、推理温度以及核心指令集是系统的逻辑资产。它们属于代码（In-Code），通过版本控制保证行为的**高度确定性**。
*   **Brain (基础设施)**：模型供应商（OpenAI, DeepSeek等）、算力路由、API 凭证属于资源层。它们属于数据库（In-DB），由 Admin 动态管理，实现**经济与性能的动态平衡**。

### 1.2. 状态不可变性与单向数据流 (Immutability & Reducer)
*   **SSOT (唯一事实源)**：`AgentState` 是运行时的唯一快照。
*   **不可变更新**：所有变更必须通过 `StateUpdate` 模型，由 `apply_update` 方法合并。这种借鉴自 Redux 的模式确保了协作过程中的**可回溯性**和**并发安全**。

### 1.3. 强契约协议化 (Protocol-First Architecture)
*   **XML 标签契约**：摒弃模糊的正则匹配，强制执行严格的 XML 标签规范（`<thought>`, `<action>`, `<call>`）。
*   **自愈循环**：将错误视为一种观测（Observation），而非程序崩溃。通过将 Traceback 包装在 XML 中反馈给模型，触发其自我修复（Reflection）。

---

## 2. 核心目录结构 (Directory Structure)

```text
apps/engine/core/
├── agent/
│   ├── base.py         # 抽象驱动基类，定义智能体交互接口
│   ├── llm_agent.py    # LLM 驱动实现，负责消息格式化与推理发起
│   ├── runtime.py      # 执行内核，管理生命周期、中间件驱动及 ReAct 循环
│   ├── factory.py      # 组装工厂，负责将 Soul (代码) 与 Brain (DB) 实例化
│   └── state.py        # 状态模型，包含 Reducer 逻辑与快照管理
├── protocol/
│   ├── schema.py       # XML 契约定义 (Thought, Action, Call, Reflection)
│   └── parser.py       # 强健的协议解析引擎，处理流式标签未闭合及 JSON 提取
├── prompt/
│   └── compiler.py     # 基于 Jinja2 的提示词编译器，实现声明式上下文组装
├── middleware/
│   ├── base.py         # 中间件契约，定义 pre_inference / post_inference 钩子
│   ├── context.py      # 上下文管理器，实现滑动窗口压缩与剪枝策略
│   ├── environment.py  # 环境装配器，动态注入时间、目录、权限等实时养料
│   └── logging.py      # 可观测性中间件，全量记录 State 突变与 Prompt 细节
├── registry/
│   ├── internal.py     # 身份名录，存储内置 Agent 的静态定义与逻辑灵魂
│   └── manager.py      # 资源协调服务，负责自动注册核心工具与发现机制
├── llm/
│   ├── resolver.py     # 经济调度路由，根据 Admin 策略映射 Provider/Model
│   ├── service.py      # 原子 LLM 服务层，处理重试、限流与流式传输
│   └── client_manager.py # 协议驱动管理器，根据 Provider 类型分发适配器
└── tools/
    ├── base.py         # 工具基类，提供自动 Schema 生成与装饰器接口
    └── registry.py     # 全局工具注册表，实现原子能力的统一检索
```

---

## 3. 应用的设计模式 (Design Patterns)

### 3.1. 策略模式 (Strategy Pattern)
*   **应用点**：`LLMProviderAdapter` 体系。
*   **价值**：系统可以透明地在 OpenAI, Anthropic, DeepSeek 协议之间切换，而上层业务逻辑完全无感知。

### 3.2. 责任链模式/洋葱模型 (Chain of Responsibility)
*   **应用点**：`Middleware` 执行链。
*   **价值**：实现了高度解耦的拦截机制。环境注入、上下文压缩、安全过滤等功能以插件形式插拔，不污染 Runtime 核心代码。

### 3.3. 工厂模式 (Factory Pattern)
*   **应用点**：`AgentFactory`。
*   **价值**：封装了复杂的组装逻辑。调用方只需输入 `agent_id`，工厂负责拉取内置定义、查询数据库配置、加载中间件，返回完整的运行实例。

### 3.4. 解析器模式 (Parser Pattern)
*   **应用点**：`ProtocolParser`。
*   **价值**：将非结构化的模型文本转化为结构化的 `ProtocolResponse` 领域对象，是实现强契约通信的关键。

### 3.5. 桥接模式 (Bridge Pattern)
*   **应用点**：`LLMConfigResolver`。
*   **价值**：作为“代码中的逻辑”与“数据库中的资源”之间的桥梁，实现了运行时配置的动态融合。

---

## 4. 关键功能机制 (Key Mechanisms)

### 4.1. 动态上下文工程 (Context Engineering)
利用 **Jinja2 渲染引擎** 实现。
*   **按需展示**：`{% if skill_docs %}` 逻辑确保了 Prompt 的高信息密度，不浪费任何 Token。
*   **实时注入**：`EnvironmentMiddleware` 确保模型具备“此时此刻”的意识。

### 4.2. 协作移交协议 (A2A Handoff)
*   **状态移交**：不同于 V1 的暴力递归，V2 支持带上下文的 `Handoff` 请求。
*   **递归深度保护**：Orchestrator 维护调用栈，通过 `_execute_recursive` 实现任务的优雅拆解与结果聚合。

### 4.3. 上下文压缩 (Context Pruning)
*   **滑动窗口**：`ContextManagerMiddleware` 自动监控 History 长度，执行剪枝策略。
*   **重要性保留**：在剪枝过程中优先保留 SYSTEM 消息和最新的观测值，保证模型不因上下文过长而导致注意力稀释。

---
*Autonomy - 构建最严谨的生产级智能体内核*