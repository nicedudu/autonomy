# Autonomy Engine V4.0 - 系统架构与演进备忘录

## 1. 系统架构全景 (System Architecture)

Autonomy V4.0 是一个基于 **“递归编排 (Recursive Orchestration)”** 和 **“会话中心化 (Session-Centric)”** 的通用智能体引擎。其核心设计哲学是将“意图规划”与“物理执行”彻底解耦，并通过标准化的协议与中间件实现全链路的可观测与可控性。

### 核心组件拓扑
*   **Session (物理载体)**：系统的最小隔离单元。承载 Message History、Metadata、Artifacts 和 Capability Mask。所有执行都必须依附于一个特定的 Session。
*   **Agent (执行实体)**：由 `AgentProfile`（静态规格）和 `Session`（运行时环境）绑定的逻辑实体。它本身无状态，通过 `AgentExecutor` 驱动。
*   **Orchestrator (编排大脑)**：基于 `WorkflowPipeline` 的 DAG 调度器。它解析模型产出的 `Blueprint`，计算任务依赖，并通过 `Dispatcher` 分发任务。
*   **Protocol V4.0 (通信契约)**：一套基于 XML + JSON 的混合协议，强制模型输出 `<thought>`, `<interaction>`, `<blueprint>`, `<dispatch>` 四大区块，杜绝语义模糊。
*   **Middleware (神经末梢)**：基于“钩子（Hooks）”的切面控制层。实现了日志审计 (`LoggingMiddleware`)、上下文管理等横切关注点。

---

## 2. 已完成核心模块 (Completed Core Modules)

### A. 基础设施层 (Infrastructure)
- **Session Manager**: 实现了父子会话（Parent-Child Session）的血缘追踪与物理隔离。
- **Memory Gateway**: 基于 `session_id` 的隔离产物存储，杜绝了跨会话的数据污染。
- **LLM Router**: 实现了“Agent 专属配置 > 系统默认配置”的动态算力路由（集成 Supabase）。

### B. 执行与编排层 (Execution & Orchestration)
- **Agent Executor**: 实现了带“任务催办 (Nudging)”和“拓扑融合 (Topology Fusion)”的 ReAct 循环。支持断点续传。
- **Capability Dispatcher**: 实现了“原子工具”与“子智能体”的统一分发接口。支持递归委派。
- **Prompt Architect**: 实现了基于 Few-Shot 的 `AgentProfile` 动态合成，具备“造物”能力。

### C. 协议与交互层 (Protocol & Interaction)
- **Protocol Parser V4.0**: 实现了对 XML 标签和 Markdown JSON 的鲁棒解析，具备“错误回注”自愈机制。
- **Context Engineering**: 确立了“身份 -> 准则 -> 协议 -> 样本”的金字塔提示词结构。

---

## 3. 开发进度账本 (Development Ledger)

| 阶段 | 模块 | 状态 | 关键成果 |
| :--- | :--- | :--- | :--- |
| **Phase 1** | **协议与契约** | ✅ 完成 | `schema/orchestration.py`, `protocol/parser.py` |
| **Phase 2** | **编排引擎** | ✅ 完成 | `orchestrator/pipeline.py`, `resolver.py` |
| **Phase 3** | **中间件架构** | ✅ 完成 | `middleware/base.py`, `logging.py` (含全量 Trace) |
| **Phase 4** | **递归与造物** | ✅ 完成 | `agent/architect.py`, `dispatcher.py` (递归逻辑) |
| **Phase 5** | **记忆与上下文** | ✅ 完成 | 实现 `ContextMiddleware` 与滑动窗口摘要 |
| **Phase 6** | **物理沙箱** | ⏳ 待启动 | 需实现 Docker/WASM 执行环境 |
| **Phase 7** | **架构稳定性排查与重构** | 🚀 进行中 | 实施显性状态看板，解决 8B 模型逻辑断层 |

---

## 6. 架构稳定性排查与重构 (Architecture Stabilization) - 2026-01-13

### 核心目标：构建“感知-执行-反馈”的显性闭环

1.  **状态感知层重构 (Compiler Layer)**:
    *   [ ] 在 `PromptCompiler` 中实现 `Dynamic State Fusion`。
    *   [ ] 确保任务看板 JSON 包含 `status` 与 `output_snapshot` 字段。
2.  **执行反馈闭环 (Executor Layer)**:
    *   [ ] 在 `AgentExecutor` 任务分发后强制同步 `Pipeline Snapshot` 到 Session 元数据。
    *   [ ] 优化 `_fuse_orchestration` 逻辑，支持状态增量合并。
3.  **提示词降噪 (Prompt Refactoring)**:
    *   [ ] 合并冗余的任务进度展示区域。
    *   [ ] 精简协议禁令，提升 8B 模型有效注意力。


当前系统已经具备了强大的“逻辑编排”能力，但在面对超长对话时仍面临 Context Window 限制。

**立即启动的任务：阶段五 - 分层记忆引擎**
1.  **ContextMiddleware**: 实现 `pre_inference` 钩子，对 `session.history` 进行滑动窗口裁剪。
2.  **Summary Engine**: 引入异步摘要机制，将被裁剪的历史转化为 `Summary Artifact` 重新注入 Prompt。
3.  **Vector Store**: 为长期记忆引入向量检索能力。

---

## 5. 工程准则与反思 (Engineering Principles)

在之前的协作中，我们确立了以下不可动摇的铁律：

1.  **严禁补丁式开发**：遇到问题（如解析错误），必须从**架构根源**（如 Prompt 引导、Schema 定义）解决，而不是在代码里写 `if/else` 兼容。
2.  **Session 强隔离**：任何数据共享都必须通过显式的 `Arguments` 传递或 `Artifact` 引用，严禁全局变量共享。
3.  **工具优先 (Tool-First)**：在 Prompt 中强制引导模型“能用工具解决的，绝不瞎编乱造；能用现有工具的，绝不申请新专家”。
4.  **真切性审计**：测试必须基于**真实 LLM、真实数据库、真实文件系统**。Mock 仅用于单元测试，集成测试必须见血（Log）。
5.  **字段名即契约**：数据库列名、Pydantic 字段名、Prompt 变量名必须**三位一体**，严禁出现 `identifier` vs `agent_id` 这种二义性。

---
*Last Updated: 2026-01-12*
