# Autonomy 技术架构白皮书 (v2.0)

## 1. 架构总览

Autonomy 采用 **控制平面 (Control Plane) 与 执行平面 (Execution Plane) 分离** 的微服务架构。系统以 Python 编写的 **Engine** 为核心大脑，通过 WebSocket 和 REST API 与 Next.js 构建的 **Web 终端** 进行实时交互。

### 核心组件拓扑

```mermaid
graph TD
    User[用户/董事长] -->|指令/自然语言| Web[Web 指挥中心 (Next.js)]
    Web -->|WebSocket (实时流)| Engine[Autonomy Engine (Python/FastAPI)]
    Web -->|HTTP (配置/管理)| Supabase[Supabase (PostgreSQL)]
    
    subgraph "Autonomy Engine"
        API[API Server] --> Orchestrator[编排器]
        Orchestrator --> Bus[通信总线 (CommunicationBus)]
        
        Bus <--> CEO[CEO Agent (调度核心)]
        Bus <--> CPO[CPO Agent (选品)]
        Bus <--> SCM[SCM Agent (供应链)]
        
        CEO & CPO & SCM --> LLM[LLM Factory]
    end
    
    LLM -->|API Call| OpenAI/Anthropic/DeepSeek
    Engine -->|Config Sync| Supabase
```

---

## 2. 智能体核心机制 (Agent Internals)

### 2.1 调度与分发 (The Dispatch System)

在 v2.0 架构中，我们确立了 **以 CEO 为绝对核心** 的调度体系。

*   **入口收敛**：所有用户指令默认路由至 `CEO Agent`。
*   **语义分发**：CEO 解析指令，识别需介入的专家（如“选品”-> CPO），通过 `@mention` 机制在内部总线上发布任务。
*   **任务委托 (Delegation)**：系统监听 CEO 的输出流，实时捕获 `@agent_id` 标签，自动触发 `task_delegation` 事件唤醒子 Agent。

### 2.2 思考引擎 (Reasoning Engine)

每个 Agent 内部运行一个 **ReAct (Reason + Act)** 循环：
1.  **Thought**：基于当前观测，进行内心独白与逻辑推演。
2.  **Plan**：拆解下一步动作（调用工具或回复消息）。
3.  **Action**：执行具体的 API 调用或数据库查询。
4.  **Observation**：获取执行结果，修正下一步计划。

### 2.3 模型工厂 (LLM Factory)

为了平衡成本与能力，Engine 内置了动态 LLM 路由层：
*   **多供应商支持**：原生适配 OpenAI (GPT-4o), Anthropic (Claude 3.5 Sonnet), DeepSeek。
*   **角色适配**：
    *   **CEO/CPO**：默认使用高推理能力的 GPT-4o 或 Claude 3.5。
    *   **SCM/客服**：使用高性价比模型处理标准化任务。
*   **流式异步**：底层完全基于 `asyncio`，确保 Token 级实时传输。

---

## 3. 通信与交互 (Communication Layer)

### 3.1 实时流式传输 (Real-time Streaming)
Engine 端实现了全链路的异步流式传输，移除了所有同步 I/O 阻塞：
*   **LLM 流**：模型生成的文本实时推送到前端。
*   **总线流**：Agent 间的协作消息（如 CEO 指派 CPO）通过 WebSocket 广播，用户可实时“旁听”数字员工的会议。

### 3.2 数据协议
*   **Message Model**：定义了 `sender`, `recipient`, `subject`, `content` 的标准结构。
*   **Markdown渲染**：前端利用 `TextDecoder` 和 Markdown 组件，支持复杂的思考标签 `<think>` 折叠显示，提供透明的决策解释性。

---

## 4. 数据与配置中心 (Data Layer)

利用 **Supabase (PostgreSQL)** 实现“配置即代码”：

*   **Prompt 热更新**：Agent 的 System Prompt 存储在云端，调整人设无需重启服务。
*   **长期记忆 (Long-term Memory)**：
    *   **知识库**：存储历史选品报告、供应商白名单。
    *   **会话记录**：持久化聊天历史，支持跨 Session 的上下文记忆。

---

## 5. 扩展性设计

*   **插件化 Agent**：新的 Agent 只需继承 `BaseAgent` 并注册到数据库，Engine 重启后即可自动装载。
*   **工具标准化 (MCP)**：工具层遵循 Model Context Protocol，提供标准化的 `input_schema`，便于 LLM 精准调用。

*最后更新: 2025-12-30*
