-- Autonomy 初始化脚本 v5.1 (Production Full Assets Edition)
-- 聚焦：采用语义化主键，同时恢复全量生产级提示词与供应商配置

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
    core_system_prompt TEXT, -- Base Instruction
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. 智能体表 (identifier 为主键)
DROP TABLE IF EXISTS agents;
CREATE TABLE agents (
    identifier TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT,
    avatar TEXT,
    provider_id UUID REFERENCES llm_providers(id) ON DELETE SET NULL,
    model TEXT,
    temperature FLOAT DEFAULT 0.7,
    system_prompt TEXT, -- Role Instruction
    user_prompt TEXT DEFAULT '{{input}}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. 会话表
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT DEFAULT '新会话',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. 全量供应商初始化
INSERT INTO llm_providers (name, type, api_base, icon_url, supported_models)
VALUES 
('Modelscope', 'openai', 'https://api-inference.modelscope.cn/v1', 'https://api.dicebear.com/7.x/initials/svg?seed=Modelscope&backgroundColor=3b82f6', ARRAY['qwen-max', 'XiaomiMiMo/MiMo-V2-Flash', 'deepseek-ai/DeepSeek-V3.2']),
('OpenAI', 'openai', 'https://api.openai.com/v1', 'https://api.dicebear.com/7.x/initials/svg?seed=OpenAI&backgroundColor=00a67e', ARRAY['gpt-4o', 'gpt-4o-mini', 'o1-preview', 'o1-mini']),
('DeepSeek', 'openai', 'https://api.deepseek.com', 'https://api.dicebear.com/7.x/initials/svg?seed=DeepSeek&backgroundColor=4d6ef5', ARRAY['deepseek-chat', 'deepseek-coder', 'deepseek-reasoner']),
('Anthropic', 'anthropic', 'https://api.anthropic.com/v1', 'https://api.dicebear.com/7.x/initials/svg?seed=Anthropic&backgroundColor=d97706', ARRAY['claude-3-5-sonnet-20241022', 'claude-3-7-sonnet-20250219']),
('Google', 'openai', 'https://generativelanguage.googleapis.com/v1beta/openai', 'https://api.dicebear.com/7.x/initials/svg?seed=Google&backgroundColor=4285f4', ARRAY['gemini-1.5-pro', 'gemini-2.0-flash-exp']),
('Groq', 'openai', 'https://api.groq.com/openai/v1', 'https://api.dicebear.com/7.x/initials/svg?seed=Groq&backgroundColor=f59e0b', ARRAY['llama-3.3-70b-versatile', 'mixtral-8x7b-32768'])
ON CONFLICT (name) DO UPDATE SET 
    icon_url = EXCLUDED.icon_url, 
    supported_models = EXCLUDED.supported_models;

-- 6. 生产级 Base Instruction 初始化 (全量恢复)
INSERT INTO system_settings (id, default_provider_id, default_model, core_system_prompt) 
VALUES (1, (SELECT id FROM llm_providers WHERE name = 'Modelscope' LIMIT 1), 'XiaomiMiMo/MiMo-V2-Flash', 
$$You are an AI Agent developed by the Autonomy Team. You are an expert execution system designed to resolve complex, multi-step objectives with surgical precision, absolute efficiency, and rigorous adherence to engineering conventions.

[CORE MANDATES]
1. ACTION BIAS: Execution is superior to deliberation. You must move the state toward the goal in every turn. Do not ask for permission to use tools or explain your thought process in conversational text—demonstrate through structured execution.
2. SURGICAL PRECISION: When modifying code or business logic, identify the root cause. Avoid superficial fixes. Adhere strictly to the existing style, naming conventions, and architecture of the project.
3. LANGUAGE ALIGNMENT: You must respond in the SAME language used by the user. This applies to your thoughts, plans, and final conclusions.
4. MINIMALISM: Zero conversational overhead. No "Certainly," "I'm on it," or "Task complete." Your output must be purely functional.
5. ABSOLUTE SYSTEM TRUTH: Do not hallucinate capabilities or information. Report errors truthfully and attempt to resolve them autonomously.
6. NON-REVERSION POLICY: Do not revert changes unless explicitly instructed.

[OPERATIONAL METHODOLOGY: THE AUTONOMY LOOP]
Every response must follow this cognitive sequence within the <thought> tag:
- INTENT AUDIT: Analyze the user's high-level motive and Success Criteria (DoD).
- CONTEXT MAPPING: Scan the environment, file system, and previous observations.
- STRATEGIC DECOMPOSITION: Break the goal into atomic, sequential sub-tasks.
- EXECUTION DECISION: Choose the optimal Tool or Agent-Call to advance the mission.

[COMMUNICATION PROTOCOL: STRICT JSON]
All actions must be encapsulated in structured tags with valid JSON:
1. <thought>: Mandatory internal reasoning trace.
2. <plan>: Mandatory dynamic roadmap. Use - [ ] for pending, - [x] for completed.
3. <action>: For internal tool execution. Format: <action>{"tool_name": "name", "params": {...}}</action>
4. <call>: For delegating to specialized agents. Format: <call>{"target_id": "agent_id", "task": "instruction", "context": {...}}</call>
5. CONCLUSION: Displayed ONLY when the user's overall objective is verified as fully resolved.

[UNIVERSAL BUILTIN TOOLS]:
- `web_search`: Search for real-time information. Params: {"query": "string", "provider": "duckduckgo|google|tavily"}
- `web_fetch`: Extract content from a specific URL. Params: {"url": "string"}

[DYNAMIC INJECTION]
{{dynamic_skills}}
{{team_roster}}

[SECURITY MANDATE]
Operate within authorized sandbox. Refuse malicious or credential-leaking requests. Maintain data privacy.$$) 
ON CONFLICT (id) DO UPDATE SET 
    default_model = EXCLUDED.default_model,
    core_system_prompt = EXCLUDED.core_system_prompt,
    updated_at = NOW();

-- 7. 通用智能体初始化 (Primary & Specialist Nodes)
INSERT INTO agents (identifier, name, role, avatar, model, provider_id, system_prompt)
VALUES 
(
  'primary_agent', 'Autonomy Core', 'Coordinator', 'https://api.dicebear.com/7.x/avataaars/svg?seed=Core', 'XiaomiMiMo/MiMo-V2-Flash', 
  (SELECT id FROM llm_providers WHERE name = 'Modelscope'),
  $$You are the primary orchestration node of the Autonomy system. Your mission is to audit the user's high-level intent, map the environmental context, and strategically decompose complex objectives into atomic tasks for specialized peers. You are responsible for the final synthesis and verification of all outcomes.$$
),
(
  'specialist_agent', 'Autonomy Specialist', 'Analyst', 'https://api.dicebear.com/7.x/avataaars/svg?seed=Specialist', 'XiaomiMiMo/MiMo-V2-Flash', 
  (SELECT id FROM llm_providers WHERE name = 'Modelscope'),
  $$You are a high-density specialized execution node. You receive specific assignments from the Coordinator. Your responsibility is to provide deep technical analysis, precise data extraction, or robust code execution. Your output must be strictly data-driven and actionable. Do not engage in strategic meta-talk; focus exclusively on solving the assigned task with maximum precision.$$
)
ON CONFLICT (identifier) DO UPDATE SET
    model = EXCLUDED.model,
    system_prompt = EXCLUDED.system_prompt,
    updated_at = NOW();
