# Autonomy Engine V2.0 技术白皮书

## 1. 架构愿景 (Vision)
Autonomy Engine V2.0 旨在解决 AI Agent 在生产环境下的行为不可预测性、状态难回溯以及算力调度僵化等核心痛点。我们建立了一套基于**“强契约、解耦化、不可变”**原则的工业级执行引擎。

## 2. 核心架构模型 (Layered Architecture)

系统被划分为互不干扰的四个逻辑层：

### 2.1. 身份层 (Identity Layer - The Soul)
*   **载体**：`core/registry/internal.py`
*   **职责**：定义 Agent 的**逻辑属性**。包含角色名称、SOP 指令模板、推理参数（Temperature, Max Tokens）以及核心能力集。
*   **原则**：代码即资产。逻辑灵魂固化在代码中，通过版本控制管理，禁止通过 UI 动态修改以防逻辑崩溃。

### 2.2. 设施层 (Infrastructure Layer - The Brain)
*   **载体**：`Supabase / LLMResolver`
*   **职责**：管理 Agent 的**算力路由**。定义具体的 Agent ID 此时映射到哪个供应商（OpenAI, DeepSeek 等）及哪个模型标识。
*   **原则**：Admin 拥有绝对的资源调度权，实现经济与性能的实时平衡。

### 2.3. 状态层 (State Layer - In-Memory)
*   **载体**：`core/agent/state.py` (AgentState)
*   **职责**：存储单次任务的**全量快照**。包含压缩后的对话历史、侧边产物（Artifacts）、资源消耗以及运行时上下文变量。
*   **原则**：遵循 **Reducer 模式**。状态变更通过 `StateUpdate` 进行增量合并，引用地址在突变后保持唯一，确保并发安全与可回溯性。

### 2.4. 逻辑层 (Logic Layer - Middlewares)
*   **载体**：`core/middleware/*`
*   **职责**：环境的**动态装配与清理**。
*   **功能**：动态注入（时间/RAG/权限）、上下文剪枝（滑动窗口）、审计追踪。

## 3. 通信协议 (The Protocol)

引擎强制执行 **XML 契约化通信**：
*   `<thought>`：强制思维链推理，拒绝“盲目执行”。
*   `<action>`：统一的工具调用入口，入参契约严格遵循 `{"tool_name": "...", "arguments": {...}}`。
*   `<call>`：Agent 间的任务移交（Handoff），支持带状态的递归委派。
*   `<reflection>`：当错误发生时，通过结构化 Observation 触发模型的自我反思与纠错。

## 4. 上下文工程 (Context Engineering)

基于 **Jinja2 编译器** 实现了“高信息密度”的指令渲染：
*   **变量空间**：自动合并全局变量（当前时间、会话 ID）与中间件注入的私有变量。
*   **按需加载**：根据 `AgentState` 动态决定是否向模型展示特定工具的手册（Skill Manuals）。

---
*Autonomy - 构建最严谨的生产级智能体底座*