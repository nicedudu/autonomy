-- Autonomy 初始化脚本 v6.1 (Production Logic & Assets Edition)
-- 修复：恢复全量供应商资产，同时对齐 V2.0 身份与大脑分离架构

-- 1. LLM 供应商表
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

-- 2. 系统设置表
CREATE TABLE IF NOT EXISTS system_settings (
    id SERIAL PRIMARY KEY,
    default_provider_id UUID REFERENCES llm_providers(id) ON DELETE SET NULL,
    default_model TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. 智能体调度映射表 (路由：ID -> 大脑)
DROP TABLE IF EXISTS agents;
CREATE TABLE agents (
    identifier TEXT PRIMARY KEY, -- 对应代码中的 agent_id
    provider_id UUID REFERENCES llm_providers(id) ON DELETE SET NULL,
    model TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. 恢复全量供应商数据
INSERT INTO llm_providers (name, type, api_base, icon_url, supported_models)
VALUES 
('Modelscope', 'openai_compatible', 'https://api-inference.modelscope.cn/v1', 'https://api.dicebear.com/7.x/initials/svg?seed=Modelscope', ARRAY['qwen-max', 'XiaomiMiMo/MiMo-V2-Flash', 'deepseek-ai/DeepSeek-V3.2']),
('OpenAI', 'openai', 'https://api.openai.com/v1', 'https://api.dicebear.com/7.x/initials/svg?seed=OpenAI', ARRAY['gpt-4o', 'gpt-4o-mini', 'o1-preview', 'o1-mini']),
('DeepSeek', 'openai_compatible', 'https://api.deepseek.com', 'https://api.dicebear.com/7.x/initials/svg?seed=DeepSeek', ARRAY['deepseek-chat', 'deepseek-coder', 'deepseek-reasoner']),
('Anthropic', 'anthropic', 'https://api.anthropic.com/v1', 'https://api.dicebear.com/7.x/initials/svg?seed=Anthropic', ARRAY['claude-3-5-sonnet-20241022', 'claude-3-7-sonnet-20250219']),
('Google', 'openai_compatible', 'https://generativelanguage.googleapis.com/v1beta/openai', 'https://api.dicebear.com/7.x/initials/svg?seed=Google', ARRAY['gemini-1.5-pro', 'gemini-2.0-flash-exp']),
('Groq', 'openai_compatible', 'https://api.groq.com/openai/v1', 'https://api.dicebear.com/7.x/initials/svg?seed=Groq', ARRAY['llama-3.3-70b-versatile', 'mixtral-8x7b-32768'])
ON CONFLICT (name) DO UPDATE SET 
    api_base = EXCLUDED.api_base,
    supported_models = EXCLUDED.supported_models;

-- 5. 初始化全局默认配置
INSERT INTO system_settings (id, default_model, default_provider_id) 
VALUES (1, 'XiaomiMiMo/MiMo-V2-Flash', (SELECT id FROM llm_providers WHERE name = 'Modelscope' LIMIT 1))
ON CONFLICT (id) DO UPDATE SET 
    default_model = EXCLUDED.default_model,
    default_provider_id = EXCLUDED.default_provider_id;

-- 6. 初始化内置 Agent 调度映射 (身份 -> 大脑)
-- 这一步至关重要：V2.0 引擎会强制从这张表读取配置
INSERT INTO agents (identifier, model, provider_id)
VALUES 
(
  'primary_agent', 'XiaomiMiMo/MiMo-V2-Flash', 
  (SELECT id FROM llm_providers WHERE name = 'Modelscope' LIMIT 1)
),
(
  'researcher', 'deepseek-chat', 
  (SELECT id FROM llm_providers WHERE name = 'DeepSeek' LIMIT 1)
)
ON CONFLICT (identifier) DO UPDATE SET
    model = EXCLUDED.model,
    provider_id = EXCLUDED.provider_id;
