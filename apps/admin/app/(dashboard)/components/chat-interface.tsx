"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@autonomy/ui/components/button"; // Adjust import path based on workspace
import { Input } from "@autonomy/ui/components/input"; // Adjust import path
import { ScrollArea } from "@autonomy/ui/components/scroll-area";
import { Send, Loader2, ChevronDown, ChevronRight, Terminal } from "lucide-react";
import { parseMixedProtocol, ParsedProtocol } from "@/lib/stream-parser";
import { PlanWidget } from "./plan-widget";
import { cn } from "@autonomy/ui/lib/utils";

interface Message {
  id: string;
  role: "user" | "assistant" | "tool" | "error";
  content: string;
  parsed?: ParsedProtocol;
  agentName?: string;
  sourceTask?: string; // ID of the parent task if this is a sub-agent event
}

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll
  const scrollToBottom = () => {
    if (scrollRef.current) {
        const scrollArea = scrollRef.current.querySelector('[data-radix-scroll-area-viewport]');
        if (scrollArea) {
             scrollArea.scrollTop = scrollArea.scrollHeight;
        }
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:8000/api/chat/stream", { 
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: userMsg.content }),
      });

      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      const assistantMsgId = (Date.now() + 1).toString();
      let currentAssistantMsg: Message = {
        id: assistantMsgId,
        role: "assistant",
        content: "",
        parsed: { thought: null, plan: null, calls: null, content: "" },
      };

      setMessages((prev) => [...prev, currentAssistantMsg]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n").filter((line) => line.trim() !== "");

        for (const line of lines) {
          try {
            const event = JSON.parse(line);
            const sourceTask = event.source_task; // Check for sub-task origin
            
            if (event.type === "stream") {
               // Only accumulate stream to the main assistant message if it's NOT a sub-task
               // OR decide how to show sub-task streams. 
               // For now, let's ignore sub-task *text streams* to avoid noise, 
               // or handle them in a separate "Sub-task" bubble.
               
               if (sourceTask) {
                   // Optional: Ignore or direct to a specific sub-message
                   continue; 
               }

               currentAssistantMsg.content += event.content;
               currentAssistantMsg.parsed = parseMixedProtocol(currentAssistantMsg.content);
               
               setMessages((prev) => {
                 const newMsgs = [...prev];
                 const index = newMsgs.findIndex(m => m.id === assistantMsgId);
                 if (index !== -1) {
                   newMsgs[index] = { ...currentAssistantMsg };
                 }
                 return newMsgs;
               });
            } else if (event.type === "observation") {
                 // Add a tool message
                 setMessages((prev) => [
                     ...prev, 
                     { 
                         id: Date.now().toString(), 
                         role: "tool", 
                         content: event.content,
                         sourceTask: sourceTask 
                     }
                 ]);
            } else if (event.type === "error") {
                 setMessages((prev) => [
                    ...prev,
                    { 
                        id: Date.now().toString(), 
                        role: "error", 
                        content: event.content,
                        sourceTask: sourceTask
                    }
                 ]);
            }
            // "status" events can be handled similarly
          } catch (e) {
            console.error("Error parsing stream line", e);
          }
        }
      }

    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) => [
          ...prev, 
          { id: Date.now().toString(), role: "error", content: "Failed to connect to server." }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Find the latest plan from the last assistant message (ignoring sub-tasks)
  const lastPlan = messages.slice().reverse().find(m => m.role === "assistant" && !m.sourceTask && m.parsed?.plan)?.parsed?.plan;

  return (
    <div className="flex h-screen w-full bg-background overflow-hidden">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-full min-w-0">
        <header className="h-14 border-b px-6 flex items-center justify-between bg-card/50 backdrop-blur">
            <div className="font-semibold">Autonomy Agent</div>
        </header>

        <ScrollArea className="flex-1 p-4" ref={scrollRef}>
          <div className="max-w-3xl mx-auto space-y-6 pb-10">
            {messages.map((msg) => (
              <MessageItem key={msg.id} message={msg} />
            ))}
            {isLoading && messages[messages.length-1]?.role !== 'assistant' && (
                <div className="flex items-center gap-2 text-muted-foreground animate-pulse">
                    <Loader2 className="w-4 h-4 animate-spin" /> Thinking...
                </div>
            )}
          </div>
        </ScrollArea>

        <div className="p-4 border-t bg-background">
          <form onSubmit={handleSubmit} className="max-w-3xl mx-auto flex gap-3">
            <Input 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your instruction..."
              className="flex-1"
              disabled={isLoading}
            />
            <Button type="submit" disabled={isLoading || !input.trim()}>
              <Send className="w-4 h-4" />
            </Button>
          </form>
        </div>
      </div>

      {/* Sidebar - Plan & Status */}
      <PlanWidget plan={lastPlan || null} />
    </div>
  );
}

function MessageItem({ message }: { message: Message }) {
  const [isThoughtOpen, setIsThoughtOpen] = useState(false);

  // If it's a sub-task event, render it compactly
  if (message.sourceTask) {
      return (
          <div className="ml-8 text-xs text-muted-foreground bg-muted/10 p-2 rounded-md border border-dashed flex items-center gap-2 opacity-80">
              <span className="font-mono bg-muted px-1 rounded text-[10px] uppercase">Sub-task</span>
              <span className="truncate flex-1 font-mono">{message.role === 'tool' ? 'Observation' : message.role}</span>
              <span className="text-[10px] text-muted-foreground/50">ID: {message.sourceTask}</span>
          </div>
      );
  }

  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="bg-primary text-primary-foreground px-4 py-2 rounded-2xl rounded-tr-sm max-w-[80%]">
          {message.content}
        </div>
      </div>
    );
  }

  if (message.role === "tool") {
      return (
          <div className="flex gap-3 text-xs text-muted-foreground bg-muted/30 p-2 rounded border font-mono">
              <Terminal className="w-4 h-4 mt-0.5" />
              <div className="break-all whitespace-pre-wrap line-clamp-4 hover:line-clamp-none transition-all cursor-pointer">
                  {message.content}
              </div>
          </div>
      )
  }

  if (message.role === "error") {
      return (
          <div className="text-red-500 bg-red-50 dark:bg-red-900/20 p-3 rounded text-sm">
              Error: {message.content}
          </div>
      )
  }

  // Assistant Message
  const { thought, content, calls } = message.parsed || { thought: null, content: message.content, calls: null };
  const hasContent = content && content.trim().length > 0;
  
  // Don't render empty assistant messages (unless they have thoughts/calls)
  if (!thought && !hasContent && (!calls || calls.length === 0)) return null;

  return (
    <div className="flex flex-col gap-2 max-w-[90%]">
      {thought && (
        <div className="border rounded-lg bg-muted/20 overflow-hidden">
            <div 
                className="flex items-center gap-2 px-3 py-2 text-xs font-medium text-muted-foreground cursor-pointer hover:bg-muted/30 select-none"
                onClick={() => setIsThoughtOpen(!isThoughtOpen)}
            >
                {isThoughtOpen ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                Thinking Process
            </div>
            {isThoughtOpen && (
                <div className="px-3 py-2 text-sm text-muted-foreground border-t bg-muted/10 font-mono whitespace-pre-wrap leading-relaxed">
                    {thought}
                </div>
            )}
        </div>
      )}
      
      {hasContent && (
        <div className="prose dark:prose-invert text-sm leading-7 whitespace-pre-wrap">
          {content}
        </div>
      )}

      {calls && calls.length > 0 && (
          <div className="mt-2 space-y-2">
              {calls.map((call, i) => (
                  <div key={i} className="text-xs bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 p-2 rounded flex gap-2 items-center">
                      <Loader2 className="w-3 h-3 animate-spin" />
                      Calling: <span className="font-mono font-semibold">{call.agent_id}</span> - {call.instruction}
                  </div>
              ))}
          </div>
      )}
    </div>
  );
}
