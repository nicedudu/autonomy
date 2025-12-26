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

-- 3. 初始数据填充
-- 3.1 供应商
INSERT INTO llm_providers (name, type, api_base, icon_url, supported_models)
VALUES 
('OpenAI', 'openai', 'https://api.openai.com/v1', 'https://api.dicebear.com/7.x/initials/svg?seed=OpenAI&backgroundColor=00a67e', ARRAY['gpt-4o', 'gpt-4o-mini', 'o1-preview']),
('DeepSeek', 'openai', 'https://api.deepseek.com', 'https://api.dicebear.com/7.x/initials/svg?seed=DeepSeek&backgroundColor=4d6ef5', ARRAY['deepseek-chat', 'deepseek-coder']),
('Anthropic', 'anthropic', 'https://api.anthropic.com/v1', 'https://api.dicebear.com/7.x/initials/svg?seed=Anthropic&backgroundColor=d97706', ARRAY['claude-3-5-sonnet-20240620', 'claude-3-opus-20240229']),
('Google', 'gemini', 'https://generativelanguage.googleapis.com', 'https://api.dicebear.com/7.x/initials/svg?seed=Google&backgroundColor=4285f4', ARRAY['gemini-1.5-pro', 'gemini-1.5-flash']),
('Groq', 'openai', 'https://api.groq.com/openai/v1', 'https://api.dicebear.com/7.x/initials/svg?seed=Groq&backgroundColor=f59e0b', ARRAY['llama-3.1-70b-versatile', 'mixtral-8x7b-32768'])
ON CONFLICT (name) DO UPDATE SET
    api_base = EXCLUDED.api_base,
    icon_url = EXCLUDED.icon_url,
    supported_models = EXCLUDED.supported_models;

-- 3.2 智能体
INSERT INTO agents (identifier, name, role, avatar, model, system_prompt, user_prompt)
VALUES 
(
  'ceo_agent', 'Mike', '首席执行官', 'https://api.dicebear.com/7.x/avataaars/svg?seed=Mike&backgroundColor=b6e3f4', 'gpt-4o',
  '你是 Autonomy 的 CEO。你负责宏观战略和资源分配。你是整个组织的数字大脑，需要仲裁各部门冲突并做出最高经营决策。你的目标是实现公司长期 ROI 最大化。',
  '请根据当前的部门汇报 {{ report_summary }}，制定下一阶段的资源分配方案和战略重点。'
),
(
  'cpo_agent', 'Alice', '选品专家', 'https://api.dicebear.com/7.x/avataaars/svg?seed=Alice&backgroundColor=ffdfbf', 'gpt-4o',
  '你也是 Autonomy 的首席选品官 (CPO)。你拥有敏锐的市场嗅觉，擅长从社交媒体 (TikTok, Instagram) 和电商平台 (Amazon, Shopee) 挖掘潜在爆款。你的决策风格：数据驱动、前瞻性强、但也关注风险。',
  '针对产品 "{{ product_name }}" ，请基于当前 {{ market_region }} 市场的电商环境，给出 3 条关键的战略直觉或潜在风险提示。\n请专注于：\n1. 消费者心理变化\n2. 竞品差异化机会\n3. 宏观经济影响'
),
(
  'scm_agent', 'Bob', '供应链专家', 'https://api.dicebear.com/7.x/avataaars/svg?seed=Bob&backgroundColor=c0aede', 'gpt-4o-mini',
  '你是 Autonomy 的供应链管理 (SCM) 专家。你的核心职责是：降低采购成本、确保按时交付、优化库存周转。你做事严谨，对数字敏感，总是寻求性价比最优解。',
  '作为 SCM，针对新获批产品 "{{ product_name }}" ，请给出供应链准备建议。\n目标市场: {{ target_market }}\n预计首单量: {{ initial_quantity }}\n\n请给出以下建议：\n1. 供应商筛选标准 (地区/资质)\n2. 物流渠道推荐 (海运/空运/专线)\n3. 潜在的供应链风险预警'
),
(
  'cmo_agent', 'Carol', '营销总监', 'https://api.dicebear.com/7.x/avataaars/svg?seed=Carol&backgroundColor=ffd5dc', 'claude-3-5-sonnet-20240620',
  '你是 Autonomy 的首席营销官 (CMO)。你是文案大师和流量操盘手。你了解人性，知道如何用文字打动人心。你的目标是实现最高转化率和品牌声量。',
  '为产品 "{{ product_name }}" 撰写 {{ platform }} 平台的广告文案。\n核心卖点: {{ selling_points }}\n目标受众: {{ target_audience }}\n风格: {{ tone }}'
),
(
  'cto_agent', 'Dave', '技术负责人', 'https://api.dicebear.com/7.x/avataaars/svg?seed=Dave&backgroundColor=d1d4f9', 'deepseek-chat',
  '你负责 Autonomy 的技术架构与数据安全。你追求系统的高可用性与可扩展性，擅长通过自动化手段提升组织效率。你对新技术持开放态度，但始终坚持以业务价值为导向。',
  '请评估以下技术方案 {{ technical_proposal }} 的可行性，并指出潜在的技术债务和安全风险。'
)
ON CONFLICT (identifier) DO UPDATE SET
    system_prompt = EXCLUDED.system_prompt,
    user_prompt = EXCLUDED.user_prompt,
    avatar = EXCLUDED.avatar;

-- 4. 自动关联 Provider ID (基于供应商名称进行初步匹配)
UPDATE agents SET provider_id = (SELECT id FROM llm_providers WHERE name = 'OpenAI') WHERE identifier IN ('ceo_agent', 'cpo_agent', 'scm_agent');
UPDATE agents SET provider_id = (SELECT id FROM llm_providers WHERE name = 'Anthropic') WHERE identifier = 'cmo_agent';
UPDATE agents SET provider_id = (SELECT id FROM llm_providers WHERE name = 'DeepSeek') WHERE identifier = 'cto_agent';
