# 通用智能体能力扩展框架 (Universal Agent Framework)

## 1. 技能驱动设计 (Skill-Driven Design)

在 Autonomy 中，一切垂直领域的逻辑都应通过“技能 (Skills)”来扩展。系统内核保持领域无关性。

## 2. 技能包构造规范

每个技能包必须存放于 `apps/engine/agents/skills/` 的子目录下，其核心文件为 `SKILL.md`。

### 2.1 结构定义
- **Metadata (YAML)**: 定义技能名称、简介、适用场景。
- **Instructions (Markdown)**: 详细的分步操作指南 (SOP)。
- **Scripts**: (可选) 实现具体的物理逻辑。

## 3. 渐进式激活机制 (Progressive Activation)

为保证效率，技能加载分为两个阶段：
1. **索引加载**: 系统扫描所有技能的描述，建立索引。
2. **内容注入**: 只有当任务意图匹配某项技能时，系统才将完整的 Markdown 指令注入到上下文。

## 4. 开发工作流

1. **新建目录**: 创建技能专属文件夹。
2. **编写清单**: 定义 `SKILL.md`。
3. **注册工具**: 如果涉及新 API，在 `tools.json` 中定义 Schema 并在 `tools/` 目录下实现。
4. **验证**: 测试智能体在相关场景下能否准确“激活”并“遵循”该技能。