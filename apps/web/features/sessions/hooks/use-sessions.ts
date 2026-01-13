
import { useState, useCallback, useEffect } from 'react';
import { supabase } from '@/lib/supabase';

export interface Session {
  id: string;
  title: string;
  created_at: string;
}

export function useSessions() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [sessionTitle, setSessionTitle] = useState("新会话");

  const fetchSessions = useCallback(async () => {
    const { data } = await supabase
      .from("chat_sessions")
      .select("*")
      .order("created_at", { ascending: false });
    if (data) setSessions(data as Session[]);
  }, []);

  const createSession = useCallback(async (title: string = "新会话") => {
    const { data } = await supabase
      .from("chat_sessions")
      .insert([{ title }])
      .select()
      .single();
    if (data) {
      const newSession = data as Session;
      setSessions(prev => [newSession, ...prev]);
      return newSession;
    }
    return null;
  }, []);

  const updateSessionTitle = useCallback(async (id: string, title: string) => {
    if (!id || !title.trim()) return;
    await supabase.from("chat_sessions").update({ title }).eq("id", id);
    setSessions(prev => prev.map(s => s.id === id ? { ...s, title } : s));
  }, []);

  const deleteSession = useCallback(async (id: string) => {
    const { error } = await supabase.from("chat_sessions").delete().eq("id", id);
    if (error) return false;
    setSessions(prev => prev.filter(s => s.id !== id));
    return true;
  }, []);

  useEffect(() => {
    fetchSessions();
  }, []);

  return {
    sessions,
    currentSessionId,
    setCurrentSessionId,
    sessionTitle,
    setSessionTitle,
    createSession,
    updateSessionTitle,
    deleteSession,
    refreshSessions: fetchSessions
  };
}
