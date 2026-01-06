# Autonomy 项目演进记录 (Moment) - 2026-01-06

## 1. 架构飞跃：Engine V2.0 生产级内核重构 (Architecture Leap)

### 1.1 灵魂与大脑的科学解耦 (Soul-Brain Separation)
- **逻辑资产化**：将智能体的“身份（Identity）”与“灵魂指令（Instructions）”固化在代码中（`core/registry/internal.py`），确立了 Agent 的行为主权，防止由于 Admin 误操作导致的逻辑崩溃。
- **算力调度外部化**：将供应商、模型路由及经济策略完全下放到 Supabase 数据库管理。实现了“逻辑归代码、算力归 Admin”的工业级设计，支持零发布、秒级动态切换模型。

### 1.2 强契约协议化执行 (Protocol-First Architecture)
- **XML 标签契约**：彻底废弃模糊的正则匹配，强制执行严格的 XML 通讯协议（`<thought>`, `<action>`, `<call>`, `<reflection>`, `<conclusion>`）。极大提高了复杂上下文下的指令遵循度和解析稳定性。
- **参数标准化**：全链路统一使用 `arguments` 契约，彻底清理了历史遗留的 `params` 等非标字段，对齐 OpenAI/MCP 行业基准。

### 1.3 状态不可变性与 Reducer 模式
- **SSOT (唯一事实源)**：重构 `AgentState` 为单向数据流模型。所有状态变更必须通过 `StateUpdate` 进行显式合并，实现了任务执行过程的“可回溯性”和“并发安全”。
- **Artifacts 剥离机制**：引入了侧边存储缓冲区，将长数据块从对话历史（History）中剥离，显著降低了 Token 损耗并延长了有效 Context 寿命。

### 1.4 洋葱模型中间件与上下文工程
- **Jinja2 动态渲染**：引入 Jinja2 作为核心提示词编译器，支持逻辑分支注入（如：`{% if skill_docs %}`），实现了极高信息密度的动态上下文组装。
- **智能修剪 (Context Pruning)**：实现了基于滑动窗口的 `ContextManagerMiddleware`，能够根据任务进度自动修剪冗余的观察过程，解决了 Agent 系统普遍存在的“注意力稀释”难题。

### 1.5 自愈协作协议 (Self-Healing & Handoff)
- **Handoff 移交机制**：重构 `Orchestrator`，实现了标准化的 A2A 状态移交协议。支持 Agent 间的控制权流转与任务递归拆解。
- **错误自愈循环**：将工具错误（TypeError, RuntimeError）结构化为 XML 观测值反馈给模型，触发其自我反思（Reflection）与参数修正，极大提升了长链路任务的成功率。

---

## 2. 工程规范与清理
- **零依赖治理**：彻底移除了脆弱的 YAML 文件注册表模式，消除了多头管理隐患。
- **目录纯净化**：清理了 `core/planning`, `core/runtime` 等 5 个冗余层级，实现扁平化、高内聚的目录结构。
- **中文专业化**：所有系统内置指令及代码注释全面切换为严谨的中文化表述，更符合本土生产环境语境。

---

## 3. 待办事项 (Next Steps)
- [ ] **State Persistence (Checkpoints)**：实现状态的持久化序列化，支持 Agent 任务的跨 Session 挂起与断点续传。
- [ ] **MCP Adapter**：开发 Model Context Protocol 适配器，支持第三方 MCP Server 的即插即用。
- [ ] **Cost Audit Middleware**：实现基于 Token 真实消耗的实时计费与预算拦截。

---
*记录人：Autonomy 核心研发智能体 (V2.0 Engine Architect)*