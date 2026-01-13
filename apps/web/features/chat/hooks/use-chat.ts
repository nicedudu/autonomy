import { useState, useCallback, useEffect } from 'react';
import { supabase } from '@/lib/supabase';
import { ENDPOINTS } from '@/lib/api';

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  agent_id?: string;
  agent_name?: string;
  agent_avatar?: string;
  timestamp: number;
  status?: string;
}

export function useChat(sessionId: string | null) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // 核心修复：切换/新建会话时清理内存状态
  useEffect(() => {
    if (!sessionId) {
      setMessages([]);
    }
  }, [sessionId]);

  const fetchMessages = useCallback(async (sid: string) => {
    setIsLoading(true);
    const { data } = await supabase
      .from("chat_messages")
      .select("*")
      .eq("session_id", sid)
      .order("created_at", { ascending: true });
    
    if (data) {
      setMessages(data.map((m: any) => ({
        id: String(m.id),
        role: m.role,
        content: String(m.content),
        agent_id: m.agent_id,
        agent_name: m.agent_name,
        agent_avatar: m.agent_avatar,
        timestamp: new Date(String(m.created_at)).getTime(),
      })));
    }
    setIsLoading(false);
  }, []);

  const sendMessage = useCallback(async (
    content: string, 
    targetAgent: { identifier: string, name: string, avatar: string },
    sid: string
  ) => {
    if (!content.trim() || isLoading) return;

    const userMsg: Message = { 
      id: `u-${Date.now()}`, 
      role: "user", 
      content, 
      timestamp: Date.now() 
    };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    let currentAssistantId = `a-${Date.now()}`;
    const initialAssistantMsg: Message = { 
      id: currentAssistantId, 
      role: "assistant", 
      content: "", 
      agent_id: targetAgent.identifier,
      agent_name: targetAgent.name, 
      agent_avatar: targetAgent.avatar, 
      timestamp: Date.now() 
    };
    setMessages(prev => [...prev, initialAssistantMsg]);

    try {
      const response = await fetch(ENDPOINTS.CHAT_STREAM, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          agent_id: targetAgent.identifier, 
          content: userMsg.content, 
          session_id: sid 
        }),
      });

      if (!response.ok) throw new Error("网络请求失败");

      const reader = response.body?.getReader();
      if (!reader) throw new Error("流读取器不可用");

      const decoder = new TextDecoder();
      let buffer = "";
      let lastAgentId = targetAgent.identifier;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const event = JSON.parse(line);
            if (event.type === "stream") {
              if (event.agent_id && event.agent_id !== lastAgentId) {
                lastAgentId = event.agent_id;
                currentAssistantId = `a-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
                setMessages(prev => [...prev, { 
                  id: currentAssistantId, 
                  role: "assistant", 
                  content: event.content, 
                  agent_id: event.agent_id,
                  agent_name: event.agent_id,
                  timestamp: Date.now() 
                }]);
              } else {
                setMessages(prev => {
                  const index = prev.findIndex(m => m.id === currentAssistantId);
                  if (index === -1) return prev;
                  const updated = [...prev];
                  updated[index] = {
                    ...updated[index],
                    content: (updated[index].content || "") + event.content,
                    agent_name: event.agent_id || updated[index].agent_name
                  };
                  return updated;
                });
              }
            } else if (event.type === "status") {
              setMessages(prev => prev.map(m => 
                m.id === currentAssistantId ? { ...m, status: event.content } : m
              ));
            }
          } catch (e) {}
        }
      }
    } catch (error) {
      console.error("Stream error:", error);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading]);

  return {
    messages,
    setMessages,
    isLoading,
    sendMessage,
    fetchMessages
  };
}
