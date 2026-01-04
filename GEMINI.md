# Autonomy 研发与执行准则 (GEMINI.md)

作为本工程的研发智能体，你必须严格遵守以下准则，并以行业顶尖 Agent 系统为设计基准，确保交付生产级的通用智能体应用。

## 1. 行业基准参考 (Industry Benchmarks)

在进行提示词工程、任务编排或技能设计时，必须参考以下顶级系统的设计模式：

- **Manus / Perplexity Pro**: 学习其“意图审计”与“多跳搜索预测”逻辑。
    - [Manus Prompt](https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools/blob/main/Manus%20Agent%20Tools%20%26%20Prompt/Prompt.txt)
    - [Manus Loop](https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools/blob/main/Manus%20Agent%20Tools%20%26%20Prompt/Agent%20loop.txt)
- **Claude Code (Anthropic)**: 学习其“防御性工程”思维与“极简主义”输出风格。
    - [Claude Code Prompt](https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools/blob/main/Anthropic/Claude%20Code/Prompt.txt)
- **Codex CLI (OpenAI)**: 学习其“任务账本”管理与显式“进度状态”跟踪。
    - [Codex CLI Prompt](https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools/blob/main/Open%20Source%20prompts/Codex%20CLI/Prompt.txt)
- **OpenAI Skills Standard**: 严格遵循其“定义与实现分离”的规范。
    - [Codex Skills API](https://developers.openai.com/codex/skills)

## 2. 核心参考文档 (Internal Documentation)

在执行具体模块开发前，必须查阅并遵守以下文档规范：

- `docs/TECHNICAL_WHITE_PAPER.md`: **技术白皮书**。包含系统分层架构（Orchestrator/Executor）、全局共识事实库（Global Facts）及结构化通讯协议的详细定义。
- `docs/UNIVERSAL_AGENT_FRAMEWORK.md`: **通用框架规范**。定义了技能（Skills）的目录结构、`SKILL.md` 的编写准则以及“渐进式激活”的生命周期。
- `docs/USER_MANUAL.md`: **用户手册**。从用户视角描述系统交互模式及核心功能（如 Researcher）的预期行为。
- `docs/VISION_AND_ROADMAP.md`: **演进蓝图**。记录当前已达成的能力及未来的多模态与自主进化规划。
- `moment.md`: **项目里程碑**。实时记录最新的架构更新与关键修复。

## 3. 核心概念：智能体技能 (Agent Skills)

技能是系统的核心灵魂，严格对齐 OpenAI Codex 官方标准：

- **本质定义**: 技能是自包含的领域能力包（Domain Capability Bundle）。
- **文件规范**:
    - **`SKILL.md`**: 核心定义文件。YAML Header 用于索引，Markdown Body 用于行为塑造。
    - **渐进式披露**: 系统仅在思考过程（`<thought>`）中明确触发该技能 ID 时，才动态注入详细指令。

## 4. 生产级代码准则 (Production Coding Standards)

- **协议标准化**: 严格遵循原生 SDK 调用。禁止底层强行拦截参数，路由由 `LLMFactory` 调度。
- **基础设施优先**: 通用逻辑必须抽象至 `core/utils`。
- **防御性编程**: 显式处理 421/400 异常，Pydantic 模型必须具备非标数据宽容度。
- **中文化注释**: **所有代码注释、逻辑说明必须使用专业、严谨的中文**。
- **透明化开发**: 控制台必须实时展示 LLM 请求上下文、Token 流及工具 I/O。

## 5. 任务闭环与核心禁令

- **意图审计**: 面对需求先调研，严禁凭空假设。
- **自动纠错**: 崩溃后必须实施架构级修复，严禁只用 `try-except` 掩盖。
- **禁止回退**: 严禁撤销已有的稳定性加固或标准化重构。

---
*Autonomy - 通用智能体调度与执行引擎*
