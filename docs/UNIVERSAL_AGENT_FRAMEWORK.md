# Nexus V4+: 通用自主智能体架构 (Universal Autonomous Agent Framework)

## 1. 设计愿景
Nexus V4+ 旨在构建一个领域无关（Domain-Agnostic）的、具备高度自主执行能力的 Agent 操作系统。系统通过加载不同的 **Skills (能力包)** 来适配特定的商业场景，如跨境电商、软件工程或数据分析。

---

## 2. 核心架构：三层驱动模型

### 2.1 宪法层 (The Constitution)
定义 Agent 的底层人格与安全边界。此层提示词是静态的、全局的。
*   **原则**: 简洁、直接、行动导向。
*   **核心逻辑**: 必须先思考 (`thought`)，再规划 (`plan`)，最后执行 (`action`)。
*   **安全**: 严禁执行超出沙盒权限的操作。

### 2.2 循环层 (The Autonomous Loop)
借鉴 Manus 的设计，系统强制执行以下闭环：
1. **分析 (Analyze)**: 结合 `User Input` 与上轮 `ActionResult`。
2. **决策 (Decide)**: 决定是调用 `Skill`、委派 `Agent` 还是 `Submit` 结果。
3. **规划 (Plan)**: 维护并展示一个实时的任务清单（Todo List）。
4. **执行 (Act)**: 通过 JSON RPC 发起调用。
5. **观测 (Observe)**: 捕获执行结果，进入下一轮循环。

### 2.3 技能层 (The Skill Registry) —— 借鉴 Claude Code
能力完全模块化。每个 Skill 都是一个独立的 Markdown 驱动单元。
*   **路径**: `.autonomy/skills/[skill-id]/`
*   **构成**: `SKILL.md` (元数据+分步指南) + `scripts/` (可执行脚本)。
*   **加载**: 只有在 `Intent Matching` 成功后才动态加载指令，实现 **渐进式披露**。

---

## 3. 协作协议：结构化 RPC 调用

为了保证生产环境的稳定性，废除所有语义化标记，强制执行严格的 JSON 协议。

### 3.1 委派 (Delegation)
```json
<call>
{
  "target_id": "specialized_agent_id",
  "task": "明确的任务指令",
  "context_snapshot": { "key": "value" }
}
</call>
```

### 3.2 动作 (Skill Action)
```json
<action>
{
  "skill_id": "searching-google",
  "params": { "query": "latest AI trends 2026" }
}
</action>
```

---

## 4. 实施路线图

### 阶段 1：内核清洗 (Domain Detach)
- [ ] 移除 `BaseAgent` 和 `Orchestrator` 中所有关于“Mike”, “跨境电商”等业务逻辑。
- [ ] 将业务逻辑迁移至第一批 Skills：`market-intelligence`, `supply-chain-audit`。

### 阶段 2：计划管理工具化
- [ ] 实现 `update_plan` 工具，强制 Agent 每轮循环汇报进度。
- [ ] 前端 UI 实时渲染这个任务清单。

### 阶段 3：环境感知与自动注入
- [ ] 借鉴 Claude Code，在 Agent 启动时自动扫描当前目录结构，生成 `File System Map` 注入上下文。

---
*Powered by Nexus V4 Modular Engine.*
