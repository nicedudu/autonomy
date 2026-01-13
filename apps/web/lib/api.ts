
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

export const ENDPOINTS = {
  AGENTS: `${API_BASE_URL}/api/agents`,
  CHAT_STREAM: `${API_BASE_URL}/api/chat/stream`,
  CHAT_SUMMARIZE: `${API_BASE_URL}/api/chat/summarize`,
  WS_CONTROL_PANEL: (sessionId: string) => `${WS_BASE_URL}/ws/control-panel/${sessionId}`,
};
