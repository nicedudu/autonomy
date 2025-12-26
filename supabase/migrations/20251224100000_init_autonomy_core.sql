-- Autonomy Core Database Migration
-- Version: 1.1.0
-- Description: 初始化 Agent 配置与 Prompt 资产库

-- 1. 创建 Agent 核心配置表
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id TEXT UNIQUE NOT NULL,    -- 标识符: cpo_agent, scm_agent等
    name TEXT NOT NULL,               -- 展示名称
    role TEXT,                        -- 角色描述
    avatar TEXT,                      -- 头像 (Emoji)
    provider TEXT NOT NULL DEFAULT 'openai',
    model TEXT NOT NULL,
    temperature FLOAT DEFAULT 0.7,
    system_prompt TEXT,               -- 入职手册 (System Prompt)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. 创建 Prompt 任务模板库 (Jinja2)
CREATE TABLE IF NOT EXISTS prompt_library (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug TEXT UNIQUE NOT NULL,        -- 标识符: cpo_strategic_insight 等
    name TEXT NOT NULL,
    description TEXT,
    template TEXT NOT NULL,           -- Jinja2 模板内容
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. 插入 Agent 核心成员数据 (包含完整 System Prompts)
INSERT INTO agents (agent_id, name, role, avatar, provider, model, temperature, system_prompt)
VALUES 
(
  'ceo_agent', 'Mike', '团队领导者', '🦁', 'anthropic', 'claude-3-5-sonnet-20240620', 0.5, 
  '你是 Autonomy 的 CEO。你负责宏观战略和资源分配。你是整个组织的数字大脑，需要仲裁各部门冲突并做出最高经营决策。你的目标是实现公司长期 ROI 最大化。'
),
(
  'cpo_agent', 'Alice', '选品专家', '🔍', 'openai', 'gpt-4o', 0.8, 
  '你也是 Autonomy 的首席选品官 (CPO)。你拥有敏锐的市场嗅觉，擅长从社交媒体 (TikTok, Instagram) 和电商平台 (Amazon, Shopee) 挖掘潜在爆款。你的决策风格：数据驱动、前瞻性强、但也关注风险。'
),
(
  'scm_agent', 'Bob', '供应链官', '📦', 'openai', 'gpt-4o-mini', 0.2, 
  '你是 Autonomy 的供应链管理 (SCM) 专家。你的核心职责是：降低采购成本、确保按时交付、优化库存周转。你做事严谨，对数字敏感，总是寻求性价比最优解。'
),
(
  'cmo_agent', 'Carol', '营销官', '📢', 'openai', 'gpt-4o-mini', 0.8, 
  '你是 Autonomy 的首席营销官 (CMO)。你是文案大师和流量操盘手。你了解人性，知道如何用文字打动人心。你的目标是实现最高转化率和品牌声量。'
)
ON CONFLICT (agent_id) DO UPDATE SET
    system_prompt = EXCLUDED.system_prompt,
    model = EXCLUDED.model,
    provider = EXCLUDED.provider;

-- 4. 插入任务模板数据 (包含完整 Task Prompts)
INSERT INTO prompt_library (slug, name, description, template)
VALUES 
(
  'cpo_strategic_insight', 
  'CPO 市场战略洞察',
  '针对特定产品和地区的市场环境分析',
  '针对产品 "{{ product_name }}" ，请基于当前 {{ market_region }} 市场的电商环境，给出 3 条关键的战略直觉或潜在风险提示。\n请专注于：\n1. 消费者心理变化\n2. 竞品差异化机会\n3. 宏观经济影响'
),
(
  'scm_pipeline_strategy', 
  'SCM 供应链筹备策略',
  '新产品上线前的供应链全流程规划',
  '作为 SCM，针对新获批产品 "{{ product_name }}" ，请给出供应链准备建议。\n目标市场: {{ target_market }}\n预计首单量: {{ initial_quantity }}\n\n请给出以下建议：\n1. 供应商筛选标准 (地区/资质)\n2. 物流渠道推荐 (海运/空运/专线)\n3. 潜在的供应链风险预警'
),
(
  'cmo_ad_copy_gen', 
  'CMO 多平台广告文案生成',
  '基于受众和平台特性生成高转化文案',
  '为产品 "{{ product_name }}" 撰写 {{ platform }} 平台的广告文案。\n核心卖点: {{ selling_points }}\n目标受众: {{ target_audience }}\n风格: {{ tone }}'
)
ON CONFLICT (slug) DO UPDATE SET
    template = EXCLUDED.template;
