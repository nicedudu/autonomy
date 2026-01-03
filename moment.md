# Autonomy 项目演进记录 (Moment) - 2025-12-31

## 1. 架构飞跃：Nexus V4 通用智能体引擎 (Manus-like)
### 1.1 内核领域无关化
- **去业务化重构**：删除了所有硬编码的 `ceo_agent`, `cpo_agent` 等行业角色类。
- **通用执行节点**：确立了 `primary_agent` (协调者) 和 `specialist_agent` (执行者) 作为系统基础原型。
- **配置驱动**：实现了 Agent Manifest (YAML) 与数据库配置的无缝同步，DB 成为生产环境的唯一事实来源。

### 1.2 强大的内置工具链 (Built-in Tools)
- **Web Search (ddgs)**：参考 Qwen-code 实现了多驱动搜索，默认使用免费的 DuckDuckGo (ddgs)，支持位置参数调用以保证极致的 API 兼容性。
- **Web Fetch (bs4)**：实现了具备 SSRF 防护和内容降噪（自动过滤导航/页脚）的网页抓取工具，支持智能截断保护上下文窗口。
- **执行闭环**：实现了 **Thought -> Action (Tool) -> Observation** 的多轮推理循环，工具输出实时通过 [Tool Out] 日志和前端流回传。

### 1.3 工业级提示词系统 (Prompt Engineering)
- **分层编译架构**：
    - **Base Instruction (基础指令)**：定义底层人格、闭环逻辑、JSON RPC 协议和语言对齐准则。
    - **Role Instruction (角色指令)**：由 Manifest 定义的特定岗位职责。
- **云端持久化**：将 Base Instruction 迁移至数据库 `system_settings` 表，支持在 Admin 中实时热修改并即时生效。
- **语言自适应**：Agent 能够识别用户输入语言，并在思考、规划和回复中自动对齐。

---

## 2. 工程化与体验优化
### 2.1 稳定性保障 (Resilience)
- **LLM 异步重试**：为异步流式接口引入了指数退避重试机制，完美解决 429 Rate Limit 问题。
- **路径鲁棒性**：工具加载器改用基于文件位置的绝对路径寻址，消除了跨平台运行时的路径报错。
- **类型安全**：将 `agents` 表主键从 UUID 改为语义化 `identifier` (TEXT)，彻底解决了前后端交互时的类型转换冲突。

### 2.2 UI/UX 极致打磨
- **Admin 升级**：新增“技能中心”可视化页面；智能体配置支持自动继承全局 LLM 设置。
- **Web 体验**：输入框默认自动获得焦点；Loading 状态简化为极简的点阵跳动动画。

---

## 3. 未来规划 (Roadmap)
- [ ] **多模态感知**：集成 Web Vision 技能，支持 Agent 对网页截图进行视觉分析。
- [ ] **复杂技能沙盒**：实现基于 Docker 或 WebAssembly 的安全代码执行环境。
- [ ] **组织智力演进**：实现技能的“自动发现与固化”逻辑，允许 Agent 跨会话沉淀经验。

---
*记录人：Gemini CLI Agent (Nexus V4 Architecture Core)*