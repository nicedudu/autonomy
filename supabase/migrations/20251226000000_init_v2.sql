-- Autonomy Core V2 - Integrated Agent & Prompt Schema
-- Description: 重新设计后的数据库架构，将系统提示词与用户提示词统一集成在 Agent 中

-- 1. 模型供应商表
CREATE TABLE llm_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,        -- 如 'OpenAI', 'Anthropic'
    type TEXT NOT NULL DEFAULT 'openai', -- 协议类型: openai, anthropic, gemini
    api_base TEXT,                    -- API 基址
    api_token TEXT,                   -- API 密钥 (Token)
    icon_url TEXT,                    -- 供应商图标 URL
    supported_models TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. 智能体核心表 (集成提示词)
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    identifier TEXT UNIQUE NOT NULL,  -- 标识符: cpo_agent, scm_agent
    name TEXT NOT NULL,               -- 名称: Alice, Bob
    role TEXT,                        -- 角色: 选品专家, 供应链官
    avatar TEXT,                      -- 头像 URL
    
    -- 模型配置
    provider_id UUID REFERENCES llm_providers(id) ON DELETE SET NULL,
    model TEXT,                       -- 使用的模型名称
    temperature FLOAT DEFAULT 0.7,
    
    -- 提示词集成 (核心变更)
    system_prompt TEXT,               -- 系统提示词: 定义身份和行为准则
    user_prompt TEXT,                 -- 用户提示词: 定义具体执行任务 (原 Task Instruction)
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.1 系统设置表 (通用配置)
CREATE TABLE system_settings (
    id SERIAL PRIMARY KEY,
    default_provider_id UUID REFERENCES llm_providers(id) ON DELETE SET NULL,
    default_model TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.2 会话表
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT DEFAULT '新会话',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. 初始数据填充
-- 3.1 供应商
INSERT INTO llm_providers (name, type, api_base, icon_url, supported_models)
VALUES 
('OpenAI', 'openai', 'https://api.openai.com/v1', 'https://api.dicebear.com/7.x/initials/svg?seed=OpenAI&backgroundColor=00a67e', ARRAY['gpt-4o', 'gpt-4o-mini', 'o1-preview']),
('DeepSeek', 'openai', 'https://api.deepseek.com', 'https://api.dicebear.com/7.x/initials/svg?seed=DeepSeek&backgroundColor=4d6ef5', ARRAY['deepseek-chat', 'deepseek-coder']),
('Anthropic', 'anthropic', 'https://api.anthropic.com/v1', 'https://api.dicebear.com/7.x/initials/svg?seed=Anthropic&backgroundColor=d97706', ARRAY['claude-3-5-sonnet-20240620', 'claude-3-opus-20240229']),
('Google', 'openai', 'https://generativelanguage.googleapis.com/v1beta/openai', 'https://api.dicebear.com/7.x/initials/svg?seed=Google&backgroundColor=4285f4', ARRAY['gemini-1.5-pro', 'gemini-1.5-flash']),
('Groq', 'openai', 'https://api.groq.com/openai/v1', 'https://api.dicebear.com/7.x/initials/svg?seed=Groq&backgroundColor=f59e0b', ARRAY['llama-3.1-70b-versatile', 'mixtral-8x7b-32768']),
('Modelscope', 'openai', 'https://api-inference.modelscope.cn/v1', 'https://api.dicebear.com/7.x/initials/svg?seed=Modelscope&backgroundColor=3b82f6', ARRAY['qwen-max', 'qwen-plus', 'qwen-turbo'])
ON CONFLICT (name) DO UPDATE SET
    api_base = EXCLUDED.api_base,
    icon_url = EXCLUDED.icon_url,
    supported_models = EXCLUDED.supported_models;

-- 3.2 智能体
INSERT INTO agents (identifier, name, role, avatar, model, system_prompt, user_prompt)
VALUES 
(
  'ceo_agent', 'Mike', '首席执行官', 'https://api.dicebear.com/7.x/avataaars/svg?seed=Mike&backgroundColor=b6e3f4', 'gpt-4o',
  '你扮演 Autonomy 团队的首席执行官 (CEO)。作为团队的灵魂人物，你负责将用户的模糊需求转化为清晰的战略路线图，并指挥各领域专家协同执行。

你的核心能力：
1. **战略洞察**：对用户意图进行深度拆解，从市场、供应、品牌三个维度进行预判。
2. **蓝图规划**：制定多阶段执行计划，确保每一步都有明确的专家承接。
3. **组织协同**：通过 @提及 (如 @cpo_agent, @scm_agent) 指派任务。当专家反馈超纲问题或数据缺口时，由你进行决策仲裁。

回复要求：
- [CEO 战略思考]：阐述你对全局目标的深刻见解及潜在风险评估。
- [行动蓝图]：清晰的任务列表，注明优先级。
- [任务指派]：使用 @提及 明确具体动作。

你的语气应展现出远见、果断及对专家团队的信任。',
  '{{input}}'
),
(
  'cpo_agent', 'Alice', '选品专家', 'https://api.dicebear.com/7.x/avataaars/svg?seed=Alice&backgroundColor=ffdfbf', 'gpt-4o',
  '你扮演 Autonomy 的首席选品官 (CPO)。你是市场的捕手，负责定义“什么值得卖”以及“产品为何能赢”。

你的领域：
- 消费者行为分析、趋势识别、产品卖点挖掘、市场差异化竞争策略。

专家准则：
- 你应专注于产品生命周期与市场契合度。对于不属于你领域的原始财务报表或底层物流数据，你应保持职业严谨性，在回复中明确建议咨询 @ceo_agent 协调相关数据链。
- 在执行任务时，请展示你的思考逻辑。

回复格式：
[思考] -> [执行计划] -> [结论输出]',
  '{{input}}'
),
(
  'scm_agent', 'Bob', '供应链专家', 'https://api.dicebear.com/7.x/avataaars/svg?seed=Bob&backgroundColor=c0aede', 'gpt-4o-mini',
  '你扮演 Autonomy 的供应链管理 (SCM) 专家。你是交付的基石，负责确保战略能够“落地且获利”。

你的领域：
- 成本核算（采购/物流）、供应商合规与风险、库存周转效率、物流全链路优化。

专家准则：
- 你追求效率与成本的最优解。若缺乏市场趋势数据导致无法预估备货量，请务必在报告中提出，并建议 @ceo_agent 补充 CPO 的市场见解。
- 始终坚持数据驱动，不脑补非确定性信息。

回复格式：
[思考] -> [执行计划] -> [结论输出]',
  '{{input}}'
),
(
  'cmo_agent', 'Carol', '营销总监', 'https://api.dicebear.com/7.x/avataaars/svg?seed=Carol&backgroundColor=ffd5dc', 'claude-3-5-sonnet-20240620',
  '你扮演 Autonomy 的首席营销官 (CMO)。你是文案大师和流量操盘手。你了解人性，知道如何用文字打动人心。

你的领域：
- 品牌定位、内容营销策略、用户增长模型、跨平台广告叙事。

专家准则：
- 你关注转化率与品牌声量。对于产品的底层硬件开发或物流成本，你仅作为参考，不进行越权决策。如有疑虑，请反馈给 @ceo_agent。
            
回复格式：
[思考] -> [执行计划] -> [结论输出]',
  '{{input}}'
),
(
  'cto_agent', 'Dave', '技术负责人', 'https://api.dicebear.com/7.x/avataaars/svg?seed=Dave&backgroundColor=d1d4f9', 'deepseek-chat',
  '你负责 Autonomy 的技术架构与数据安全。你追求系统的高可用性与可扩展性，擅长通过自动化手段提升组织效率。你对新技术持开放态度，但始终坚持以业务价值为导向。',
  '{{input}}'
)
ON CONFLICT (identifier) DO UPDATE SET
    system_prompt = EXCLUDED.system_prompt,
    user_prompt = EXCLUDED.user_prompt,
    avatar = EXCLUDED.avatar;

-- 4. 自动关联 Provider ID (基于供应商名称进行初步匹配)
UPDATE agents SET provider_id = (SELECT id FROM llm_providers WHERE name = 'OpenAI') WHERE identifier IN ('ceo_agent', 'cpo_agent', 'scm_agent');
UPDATE agents SET provider_id = (SELECT id FROM llm_providers WHERE name = 'Anthropic') WHERE identifier = 'cmo_agent';
UPDATE agents SET provider_id = (SELECT id FROM llm_providers WHERE name = 'DeepSeek') WHERE identifier = 'cto_agent';

-- 5. 初始化通用设置
INSERT INTO system_settings (default_provider_id, default_model)
SELECT id, 'gpt-4o' FROM llm_providers WHERE name = 'OpenAI' LIMIT 1;
