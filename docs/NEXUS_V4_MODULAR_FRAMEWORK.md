# Nexus V4: 模块化插件式智能体架构实施方案 (The Modular Framework)

## 1. 架构愿景：基于“技能 (Skills)”的自主进化组织

在 Nexus V4 中，我们将借鉴 **Claude Code** 的核心思想，将“技能”定义为一套**具备权限约束的、自描述的逻辑包**。

*   **智能体 (Agent)**: 只是一个持有基础身份（Identity）的容器。
*   **技能 (Skill)**: 存储在 `.autonomy/skills/` 目录下的 Markdown 文件夹，它是智能体获取能力的唯一途径。

---

## 2. 技能 (Skill) 的工程定义

每个技能由一个名为 `SKILL.md` 的核心文件驱动，其结构如下：

### 2.1 结构化元数据 (YAML Metadata)
```yaml
---
name: market-trend-analysis
description: "当需要分析 TikTok, Amazon 等平台的选品趋势并产出 PRD 时调用此技能。"
allowed-tools: [ "market_scraper", "google_search", "read_file" ]
model: "claude-3-5-sonnet-20241022" # 可选，指定该技能执行时的专用模型
priority: 10
---
```

### 2.2 教学式指令 (Markdown Instructions) —— 借鉴 Claude Code
在 YAML 之后，是提供给智能体的详细分步指南：
*   **Step 1**: 使用 `market_scraper` 抓取近 24h 飙升数据。
*   **Step 2**: 交叉比对 Google Search 的搜索热度。
*   **Step 3**: 输出符合 `templates/prd.md` 格式的报告。

---

## 3. 核心机制：渐进式披露与加载 (Progressive Disclosure)

为了平衡性能（Token 消耗）与响应速度，Nexus V4 采用三级加载机制：

1.  **启动加载 (Discovery Phase)**:
    *   Orchestrator 仅扫描所有 `SKILL.md` 的 `name` 和 `description`。
    *   建立一个轻量级的“能力名录”注入 CEO Agent。
2.  **激活加载 (Activation Phase)**:
    *   当意图匹配时，Orchestrator 询问用户/CEO：“检测到需要激活 `market-trend-analysis` 技能，是否继续？”
    *   确认后，**动态将该 Skill 的 Markdown 指令注入 System Prompt**。
3.  **按需调用 (Execution Phase)**:
    *   Skill 内部引用的 `scripts/*.py` 仅在智能体调用特定 Tool 时才被执行，不会将代码内容全量塞入对话历史。

---

## 4. 技能库的分层与优先级 (Hierarchy & Priority)

借鉴 Claude Code，Nexus V4 实施四层 Skill 覆盖逻辑：
1.  **Enterprise (`/etc/autonomy/skills/`)**: 公司级强制规范（如财务合规、品牌调性）。
2.  **Personal (`~/.autonomy/skills/`)**: 个人习惯或私有工具。
3.  **Project (`.autonomy/skills/`)**: 当前项目特定的业务逻辑（如：特定的选品规则）。
4.  **Plugin (`engine/plugins/`)**: 系统自带的基础技能。

---

## 5. 状态快照传递 (State Snapshot) —— 借鉴 Qwen-code

为了确保 Skill 在“冷启动”时能快速衔接上下文：
*   在 Skill 激活时，Orchestrator 自动执行 `Context Summary` 动作。
*   生成一个包含当前已确定事实（Facts）和待办事项（Pending）的 XML 快照，作为 Skill 启动的 **Initial Context**。

---

## 6. 开发者指南：如何创建新技能

1.  **创建目录**: `mkdir -p .autonomy/skills/my-new-skill`
2.  **编写 `SKILL.md`**: 定义 YAML 元数据和分步 Markdown 指令。
3.  **放入资源**: 将复杂的 Python 处理逻辑放入 `scripts/` 子目录。
4.  **注册**: 运行 `autonomy skills reload`。

---

## 7. 结论

Nexus V4 将 Autonomy 变成了一个**“技能热插拔”**的系统。通过引入 Claude Code 风格的 `SKILL.md`，我们实现了：
*   **极致的安全控制**: 细粒度的 `allowed-tools` 权限管理。
*   **极致的 Token 效率**: 仅在需要时加载指令，而非全量注入。
*   **极低的学习门槛**: 业务人员只需写 Markdown 就能教 AI 学会新的公司规章或工作流程。

---
*Next Action: 启动 UniversalExecutor 开发，支持 SKILL.md 的动态解析与权限路由。*