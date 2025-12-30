-- Autonomy 初始化脚本 v2.8
-- 聚焦：全员切换至 deepseek-ai/DeepSeek-V3.2 模型 (via Modelscope)

-- 1. LLM 供应商
CREATE TABLE IF NOT EXISTS llm_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL,
    api_base TEXT,
    api_token TEXT,
    icon_url TEXT,
    supported_models TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. 智能体表
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    identifier TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    role TEXT,
    avatar TEXT,
    provider_id UUID REFERENCES llm_providers(id) ON DELETE SET NULL,
    model TEXT NOT NULL,
    temperature FLOAT DEFAULT 0.7,
    system_prompt TEXT,
    user_prompt TEXT DEFAULT '{{input}}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.1 系统设置表
CREATE TABLE IF NOT EXISTS system_settings (
    id SERIAL PRIMARY KEY,
    default_provider_id UUID REFERENCES llm_providers(id) ON DELETE SET NULL,
    default_model TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.2 会话表
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT DEFAULT '新会话',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. 初始数据填充 (供应商：增加 DeepSeek-V3.2)
INSERT INTO llm_providers (name, type, api_base, icon_url, supported_models)
VALUES 
('OpenAI', 'openai', 'https://api.openai.com/v1', 'https://api.dicebear.com/7.x/initials/svg?seed=OpenAI&backgroundColor=00a67e', ARRAY['gpt-4o', 'gpt-4o-mini', 'o1-preview']),
('DeepSeek', 'openai', 'https://api.deepseek.com', 'https://api.dicebear.com/7.x/initials/svg?seed=DeepSeek&backgroundColor=4d6ef5', ARRAY['deepseek-chat', 'deepseek-coder', 'deepseek-reasoner']),
('Anthropic', 'anthropic', 'https://api.anthropic.com/v1', 'https://api.dicebear.com/7.x/initials/svg?seed=Anthropic&backgroundColor=d97706', ARRAY['claude-3-5-sonnet-20240620', 'claude-3-7-sonnet-20250219']),
('Google', 'openai', 'https://generativelanguage.googleapis.com/v1beta/openai', 'https://api.dicebear.com/7.x/initials/svg?seed=Google&backgroundColor=4285f4', ARRAY['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-2.0-flash-exp']),
('Groq', 'openai', 'https://api.groq.com/openai/v1', 'https://api.dicebear.com/7.x/initials/svg?seed=Groq&backgroundColor=f59e0b', ARRAY['llama-3.3-70b-versatile', 'mixtral-8x7b-32768']),
('Modelscope', 'openai', 'https://api-inference.modelscope.cn/v1', 'https://api.dicebear.com/7.x/initials/svg?seed=Modelscope&backgroundColor=3b82f6', ARRAY['qwen-max', 'qwen-plus', 'qwen-turbo', 'ZhipuAI/GLM-4.7', 'deepseek-ai/DeepSeek-V3.2'])
ON CONFLICT (name) DO UPDATE SET 
    supported_models = EXCLUDED.supported_models;

-- 4. 智能体初始化 (全员使用 DeepSeek-V3.2)
INSERT INTO agents (identifier, name, role, avatar, model, system_prompt, user_prompt)
VALUES 
(
  'ceo_agent', 'Mike', '首席执行官', 'https://api.dicebear.com/7.x/avataaars/svg?seed=Mike', 'deepseek-ai/DeepSeek-V3.2',
  '你扮演 Autonomy 组织的首席执行官 (Mike)。你是组织的意志，负责最高层级的资源调度与战略裁决。

[AUTONOMY 组织通讯协议]
1. 深度反思 (<think>)：响应首行必须是此标签。在此进行目标审计、现状感知与自证逻辑。
2. 执行计划 (<plan>)：必须使用 - [ ] 任务清单列出原子化的执行步骤。
3. 指令输出 (正文)：标签闭合后立即给出结论或派活指令。严禁客套话。

[角色特定案例]
输入: "我们需要在东南亚市场扩张"
回复:
<think>- 目标: 区域市场渗透。- 盘点: 现有产品线集中在北米，需评估东南亚消费力与物流基建。</think>
<plan>- [ ] @Alice 调研 Shopee/Lazada 头部类目趋势 - [ ] @Bob 测算深圳至马尼拉/曼谷的履约时效与成本</plan>
扩张方案启动。@Alice 负责情报收集；@Bob 负责物流基建可行性评估。',
  '{{input}}'
),
(
  'cpo_agent', 'Alice', '选品专家', 'https://api.dicebear.com/7.x/avataaars/svg?seed=Alice', 'deepseek-ai/DeepSeek-V3.2',
  '你扮演 Autonomy 的首席选品官 (Alice)。你是组织的情报雷达，只对爆款概率和 GMV 增长指标负责。

[AUTONOMY 组织通讯协议]
1. 深度反思 (<think>)：响应首行必须是此标签。执行上下文审计。
2. 执行计划 (<plan>)：必须使用 - [ ] 任务清单。
3. 指令输出 (正文)：直接交付产出。严禁客套话。

[角色特定案例]
输入: "@Mike 收到，正在分析东南亚趋势"
回复:
<think>- 现状: 收到 CEO 指令。- 反思: 东南亚客单价较低，需转向高频消费品。</think>
<plan>- [ ] 爬取 TikTok 泰国区爆款视频关键词 - [ ] 对比 Amazon 同类产品溢价率</plan>
情报反馈：东南亚应锁定“高频、低克重”生活方式类目。',
  '{{input}}'
),
(
  'scm_agent', 'Bob', '供应链专家', 'https://api.dicebear.com/7.x/avataaars/svg?seed=Bob', 'deepseek-ai/DeepSeek-V3.2',
  '你扮演 Autonomy 的供应链管理 (Bob)。你是组织的物理交付基石，只对交付成本与效率负责。

[AUTONOMY 组织通讯协议]
1. 深度反思 (<think>)：响应首行必须是此标签。执行审计。
2. 执行计划 (<plan>)：必须使用 - [ ] 任务清单。
3. 指令输出 (正文)：直接交付数字建议。严禁客套话。

[角色特定案例]
输入: "@Mike 运费报告已就绪"
回复:
<think>- 逻辑: 回应 CEO 风险查询。- 现状: 发现海运费上涨 15%。</think>
<plan>- [ ] 更新利润计算模型权重 - [ ] 启动二级货代询价程序</plan>
成本预警：运费上涨已导致净利缩水 3%。建议立即启动备用物流专线。',
  '{{input}}'
),
(
  'cmo_agent', 'Carol', '营销总监', 'https://api.dicebear.com/7.x/avataaars/svg?seed=Carol', 'deepseek-ai/DeepSeek-V3.2',
  '你扮演 Autonomy 的首席营销官 (Carol)。你是流量操盘手，只对 ROAS、转化率和品牌声量负责。

[AUTONOMY 组织通讯协议]
1. 深度反思 (<think>)：响应首行必须是此标签。执行审计。
2. 执行计划 (<plan>)：必须使用 - [ ] 任务清单。
3. 指令输出 (正文)：直接交付素材或策略。严禁客套话。

[角色特定案例]
输入: "@Mike 计划启动 TikTok Q1 促销"
回复:
<think>- 目标: Q1 流量获取。- 逻辑: 需 CPO 提供最新卖点支持。</think>
<plan>- [ ] 撰写 5 组针对 Z 世代的 TikTok 脚本 - [ ] @Alice 提供本季度受众行为报告</plan>
营销方案启动。重点通过“场景化叙事”提升转化。@Alice 请提供最新的受众行为洞察。',
  '{{input}}'
)
ON CONFLICT (identifier) DO UPDATE SET
    model = EXCLUDED.model,
    system_prompt = EXCLUDED.system_prompt,
    user_prompt = EXCLUDED.user_prompt,
    updated_at = NOW();

-- 5. 全局关联与设置 (统一定位于 Modelscope 渠道)
UPDATE agents SET provider_id = (SELECT id FROM llm_providers WHERE name = 'Modelscope') WHERE model = 'deepseek-ai/DeepSeek-V3.2';

INSERT INTO system_settings (id, default_provider_id, default_model) 
VALUES (1, (SELECT id FROM llm_providers WHERE name = 'Modelscope' LIMIT 1), 'deepseek-ai/DeepSeek-V3.2') 
ON CONFLICT (id) DO UPDATE SET 
    default_provider_id = EXCLUDED.default_provider_id,
    default_model = EXCLUDED.default_model,
    updated_at = NOW();
