-- Autonomy Schema Update
-- Version: 1.2.0
-- Description: 增加模型供应商表及 Token/BaseURL 支持

-- 1. 创建模型供应商表
CREATE TABLE IF NOT EXISTS llm_providers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT UNIQUE NOT NULL,        -- 如 'OpenAI', 'Anthropic', 'DeepSeek'
    api_base TEXT NOT NULL,           -- 默认 API 地址
    api_token TEXT,                   -- 全局 API Token (敏感信息建议加密存储)
    supported_models TEXT[],          -- 支持的模型列表 (数组)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. 增强 agents 表，增加覆盖字段
ALTER TABLE agents ADD COLUMN IF NOT EXISTS api_base TEXT;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS api_token TEXT;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS provider_id UUID REFERENCES llm_providers(id);

-- 3. 插入初始供应商数据
INSERT INTO llm_providers (name, api_base, api_token, supported_models)
VALUES 
(
  'OpenAI', 
  'https://api.openai.com/v1', 
  '', 
  ARRAY['gpt-4o', 'gpt-4o-mini', 'o1-preview']
),
(
  'Anthropic', 
  'https://api.anthropic.com/v1', 
  '', 
  ARRAY['claude-3-5-sonnet-20240620', 'claude-3-opus-20240229']
),
(
  'DeepSeek', 
  'https://api.deepseek.com', 
  '', 
  ARRAY['deepseek-chat', 'deepseek-coder']
)
ON CONFLICT (name) DO UPDATE SET
    api_base = EXCLUDED.api_base,
    supported_models = EXCLUDED.supported_models;
