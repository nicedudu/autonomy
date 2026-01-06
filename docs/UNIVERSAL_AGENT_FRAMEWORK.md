# Autonomy 通用智能体框架规范 (V2.0)

## 1. 智能体定义规范 (Agent Definition)

在 V2.0 中，注册一个新 Agent 必须在 `core/registry/internal.py` 中通过 `AgentDefinition` 对象进行声明。

```python
"coder_agent": AgentDefinition(
    agent_id="coder_agent",
    name="高级编码专家",
    role="Programmer",
    capabilities=["terminal_execute", "read_file", "write_file"],
    temperature=0.3, # 代码生成需要低随机性
    instruction_template=BASE_INSTRUCTION + "\n\n[角色职责]\n..."
)
```

## 2. 运行时生命周期 (The Lifecycle)

`AgentRuntime` 驱动的 ReAct 循环包含以下关键节点，开发者可通过中间件介入：

1.  **Init**: 加载 `AgentDefinition` 并初始化 `AgentState`。
2.  **Pre-Inference**: 
    *   `EnvironmentMiddleware` 注入动态变量。
    *   `ContextManagerMiddleware` 修剪历史记录。
    *   `PromptCompiler` 渲染 Jinja2 模板。
3.  **Inference**: 发起 LLM 请求。
4.  **Parse**: `ProtocolParser` 提取 XML 标签。
5.  **Dispatch**:
    *   如果是 `conclusion` -> 任务完成。
    *   如果是 `action` -> 调用 `tool_registry` 执行。
    *   如果是 `call` -> 进入 `Orchestrator` 递归移交。
6.  **Loop**: 将结果作为 `observation` 回注 `State`，进入下一轮。

## 3. 中间件开发指南 (Middleware Extension)

自定义中间件必须继承 `BaseMiddleware` 并实现对应的生命周期 Hook。

### 关键 Hook 签名：
*   `async def pre_inference(self, state: AgentState) -> Optional[StateUpdate]`
*   `async def post_inference(self, state: AgentState, raw_response: str) -> Optional[StateUpdate]`

### 最佳实践：
*   **不要直接修改 `state` 内部属性**：必须返回一个新的 `StateUpdate` 对象。
*   **保持无状态**：中间件本身不应存储针对特定任务的状态，所有的持久化应通过 `state.context` 传递。

## 4. 协作协议 (A2A Handoff)

当 Agent A 无法独立完成任务时，必须产出 `<call>` 标签。
*   **隔离性**：Agent B 拥有独立的 Context Window，不继承 Agent A 的所有 History。
*   **状态回传**：Agent B 的最终结论将以 XML 观测值形式返回给 Agent A。

---
*Autonomy - 标准化智能体协作的每一毫秒*
