# Autonomy 项目演进记录 (Moment) - 2025-12-31

## 1. Nexus V3 体验稳定化 (UI/UX & Prompt)
### 1.1 前端 UI 深度优化
- **Markdown 增强**：修复了列表（UL/OL）的渲染间隙，支持原生圆点与数字标识。
- **思维可视化**：为“深度思考”状态添加了大脑图标呼吸效果和点阵跳动省略号动画。
- **多智能体流展示**：重构了流式解析逻辑，支持 JSONL 格式。当 `agent_id` 切换时，前端会自动追加新的消息气泡，而非覆盖，实现了真正的“多人会议”感。
- **Plan 增强**：解决了执行计划中 Markdown 格式不解析的问题，并能正确处理 `<call>` 标签在计划中的展示逻辑。

### 1.2 提示词宪法同步
- 对 `library.yaml` 进行了微调，强化了执行权归还逻辑。
- 更新了 Supabase 迁移脚本，确保数据库预置数据与本地提示词资产 100% 字符级同步。

---

## 2. Nexus V4 模块化架构重构 (核心进化)
### 2.1 理念引入
- **借鉴 Qwen-code**：引入了 **上下文快照 (Context Snapshot)** 机制，显著提升了长对话下的 Token 效率。
- **借鉴 Codex**：确立了 **原子接口协议 (Atomic Interface)**，将智能体协作升级为语义 RPC 调用。
- **借鉴 Claude Code**：确立了 **Skill-based Manifest** 驱动模式，实现“配置即 Agent”。

### 2.2 关键代码实现
- **AgentManager**：实现了基于 YAML 清单（Manifest）的智能体自动发现引擎，支持延迟加载（Lazy Loading）。
- **BaseAgent (Universal Executor)**：重构为通用执行器，内置了 **Thought -> Action -> Observation** 的多轮闭环推理引擎。
- **SkillManager**：实现了动态技能加载器，支持从外部 Python 模块加载业务逻辑。
- **严格 RPC 协议**：在 `Orchestrator` 中强制执行 JSON 格式的协作调用，彻底废弃了不稳定的 `@` 语义提及。

---

## 3. 待办事项 (Next Steps)
- [ ] **Skill 指令深度集成**：进一步完善 `SkillManager`，支持从 `SKILL.md` 的 Markdown 中提取分步指令注入 Prompt。
- [ ] **状态机持久化**：将 `Orchestrator` 中的全局共识事实（Facts）持久化到数据库，支持跨会话状态恢复。
- [ ] **复杂技能测试**：将更多工具（如 SCM Bridge, Profit Calculator）转化为 V4 标准技能。

---
*记录人：Gemini CLI Agent*
