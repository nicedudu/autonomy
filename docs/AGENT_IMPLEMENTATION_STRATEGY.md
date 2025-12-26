# Autonomy 智能体实现思路与技术架构 (v1.2.0)

## 1. 核心设计哲学
Autonomy 的 Agent 不是简单的脚本，而是拥有**独立推理逻辑**的数字员工实体。

- **解耦推理与执行**: 大脑通过 LLM Factory 驱动，执行动作通过标准化 Skill 封装。
- **群体智能协作**: 模拟“数字会议室”进行跨部门辩论。
- **配置即生产力**: 通过 Supabase 云端配置，实现 Agent “性格”与“策略”的热更新。

## 2. Agent 内部结构 (The Anatomy)

### 2.1 思考引擎 (Reasoning Engine)
采用 **ReAct (Reason + Act)** 框架。Agent 在任务前会循环进行：
- **Thought**: “我现在的目标是什么？”
- **Plan**: “我应该先调用趋势猎手，再调用成本计算器。”
- **Action**: “执行 API 调用。”
- **Observation**: “观察到库存不足，调整策略。”

### 2.2 模型工厂 (LLM Factory)
- **多供应商路由**: 原生支持 OpenAI (GPT-4o) 和 Anthropic (Claude 3.5)。
- **实时配置同步**: 引擎优先从 Supabase 数据库读取 Agent 参数，回退至本地 YAML。
- **成本控制**: CEO/CPO 用高逻辑模型，SCM/CMO 用高性价比模型。

### 2.3 消息处理与总线 (The Digital Slack)
Agent 之间通过标准消息协议交互：
- **Message Model**: 定义 Sender, Recipient, Subject, Content, Type。
- **实时推送**: WebSocket 将每一条 `Message` 转化为前端的“气泡消息”和“思维节点”。

### 2.4 工具与技能集 (Toolbox & Skills)
- **MCP 兼容**: 所有工具遵循 Model Context Protocol，提供 `input_schema` 以便 LLM 精准调用。
- **原子工具**: 基础爬虫、数据库读写、API 触发器。
- **复合技能 (Skill)**: 将 SOP 封装为一键执行的技能（如“自动选品评估”）。

### 2.5 记忆系统 (Memory System)
- **短期记忆**: 存储在内存中的 Thought Chain。
- **长期记忆 (Vector DB)**: 计划集成 ChromaDB，存储成功选品案例和供应商信誉库。

## 3. 编排策略 (Orchestration)
采用 **“自研轻量级编排”**，避免第三方库的黑盒限制：
- **Orchestrator**: 中央控制塔，驱动事件循环。
- **状态机**: 追踪任务从 CPO (选品) -> SCM (供应链) -> CMO (投放) 的状态流转。

---
*最后更新: 2025-12-24*
