"use client";

import { supabase } from "@/lib/supabase";
import {
    Avatar,
    AvatarFallback,
    AvatarImage,
} from "@autonomy/ui/components/avatar";
import { Button } from "@autonomy/ui/components/button";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@autonomy/ui/components/tooltip";
import { PanelLeft } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { ChatInput } from "./components/ChatInput";
import { ExecutionWorkflow, ExecutionWorkflowEmpty } from "./components/ExecutionWorkflow";
import { HistorySidebar } from "./components/HistorySidebar";
import { MessageList } from "./components/MessageList";
import { parseProtocol } from "@/lib/stream-parser";

interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    agent_id?: string;
    agent_name?: string;
    agent_avatar?: string;
    timestamp: number;
    status?: string;
}

interface Agent {
    id: string;
    identifier: string;
    name: string;
    role: string;
    avatar: string;
}

interface WorkflowStep {
    agentId: string;
    agentName: string;
    agentRole: string;
    agentAvatar: string;
    status: "Idle" | "Thinking" | "Responding";
    parentId?: string;
}

interface Session {
    id: string;
    title: string;
    created_at: string;
}

export default function ExecutionConsole() {
    const [agents, setAgents] = useState<Agent[]>([]);
    const [sessions, setSessions] = useState<Session[]>([]);
    const [currentSessionId, setCurrentSessionId] = useState<string | null>(
        null
    );
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputValue, setInputValue] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [sessionTitle, setSessionTitle] = useState("新会话");
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [isFlowOpen, setIsFlowOpen] = useState(true);
    const [flowWidth, setFlowWidth] = useState(380);
    const [showScrollButton, setShowScrollButton] = useState(false);
    const [hasNewMessages, setHasNewMessages] = useState(false);
    const [workflowSteps, setWorkflowSteps] = useState<WorkflowStep[]>([]);

    const viewportRef = useRef<HTMLDivElement>(null);
    const isProgrammaticScroll = useRef(false);
    const agentsRef = useRef<Agent[]>([]);

    useEffect(() => {
        if (isLoading && viewportRef.current) {
            const target = viewportRef.current;
            const distanceToBottom =
                target.scrollHeight - target.scrollTop - target.clientHeight;
            if (distanceToBottom > 100) {
                setHasNewMessages(true);
            }
        }
    }, [messages, isLoading]);

    const fetchSessions = useCallback(async () => {
        const { data } = await supabase
            .from("chat_sessions")
            .select("*")
            .order("created_at", { ascending: false });
        if (data) setSessions(data as Session[]);
    }, []);

    const fetchMessages = useCallback(async (sessionId: string) => {
        setIsLoading(true);
        const { data } = await supabase
            .from("chat_messages")
            .select("*")
            .eq("session_id", sessionId)
            .order("created_at", { ascending: true });
        if (data) {
            setMessages(
                data.map((m) => {
                    const msg = m as Record<string, unknown>;
                    return {
                        id: String(msg.id),
                        role: msg.role as "user" | "assistant",
                        content: String(msg.content),
                        agent_id: msg.agent_id
                            ? String(msg.agent_id)
                            : undefined,
                        agent_name: msg.agent_name
                            ? String(msg.agent_name)
                            : undefined,
                        agent_avatar: msg.agent_avatar
                            ? String(msg.agent_avatar)
                            : undefined,
                        timestamp: new Date(String(msg.created_at)).getTime(),
                    };
                })
            );
        }
        setIsLoading(false);
    }, []);

    useEffect(() => {
        const fetchAgents = async () => {
            try {
                const response = await fetch(
                    "http://localhost:8000/api/agents"
                );
                if (!response.ok) throw new Error("无法获取智能体列表");
                const data = await response.json();
                if (data) {
                    setAgents(data);
                    agentsRef.current = data;
                }
            } catch (err) {
                console.error("Fetch agents error:", err);
            }
        };
        fetchAgents();
        fetchSessions();
    }, [fetchSessions]);

    const updateWorkflow = useCallback(
        (agentId: string, status: WorkflowStep["status"], parentId?: string) => {
            setWorkflowSteps((prev) => {
                const agent = agentsRef.current.find(
                    (a) => a.identifier === agentId
                );
                if (!agent) return prev;

                const existingIndex = prev.findIndex(
                    (s) => s.agentId === agentId
                );
                if (existingIndex !== -1) {
                    const newSteps = [...prev];
                    newSteps[existingIndex] = {
                        ...newSteps[existingIndex],
                        status,
                        // Update parentId if provided and not already set
                        parentId: parentId || newSteps[existingIndex].parentId,
                    };
                    return newSteps;
                } else {
                    return [
                        ...prev,
                        {
                            agentId: agent.identifier,
                            agentName: agent.name,
                            agentRole: agent.role,
                            agentAvatar: agent.avatar,
                            status,
                            parentId,
                        },
                    ];
                }
            });
        },
        []
    );

    const handleUpdateSessionTitle = useCallback(async () => {
        if (!currentSessionId || !sessionTitle.trim()) return;
        await supabase
            .from("chat_sessions")
            .update({ title: sessionTitle })
            .eq("id", currentSessionId);
        fetchSessions();
    }, [currentSessionId, sessionTitle, fetchSessions]);

    const handleDeleteSession = useCallback(
        async (sessionId: string) => {
            const { error } = await supabase
                .from("chat_sessions")
                .delete()
                .eq("id", sessionId);

            if (error) {
                console.error("Failed to delete session:", error);
                return;
            }

            setSessions((prev) => prev.filter((s) => s.id !== sessionId));

            if (currentSessionId === sessionId) {
                setMessages([]);
                setCurrentSessionId(null);
                setSessionTitle("新会话");
                setWorkflowSteps([]);
            }
        },
        [currentSessionId]
    );

    const handleSend = async () => {
        if (!inputValue.trim() || isLoading) return;
        let sessionId = currentSessionId;
        if (!sessionId) {
            const { data } = await supabase
                .from("chat_sessions")
                .insert([{ title: "新会话" }])
                .select()
                .single();
            if (data) {
                sessionId = (data as Session).id;
                setCurrentSessionId(sessionId);
                fetchSessions();
            }
        }
        const mentionedAgent = agents.find((a) =>
            inputValue.includes(`@${a.name}`)
        );
        const targetAgent =
            mentionedAgent ||
            agents.find((a) => a.identifier === "primary_agent");
        if (!targetAgent) return;

        const userMsg: Message = {
            id: Date.now().toString(),
            role: "user",
            content: inputValue,
            timestamp: Date.now(),
        };
        const isFirstMessage = messages.length === 0;
        setMessages((prev) => [...prev, userMsg]);
        setInputValue("");
        setIsLoading(true);

        const assistantId = (Date.now() + 1).toString();
        // Update workflow for initial agent
        updateWorkflow(targetAgent.identifier, "Thinking");

        try {
            if (isFirstMessage && sessionId) {
                fetch("http://localhost:8000/api/chat/summarize", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ content: userMsg.content }),
                })
                    .then((res) => res.json())
                    .then(async (data) => {
                        if (data.title && sessionId) {
                            setSessionTitle(data.title);
                            await supabase
                                .from("chat_sessions")
                                .update({ title: data.title })
                                .eq("id", sessionId);
                            fetchSessions();
                        }
                    })
                    .catch((err) => console.error("Summarize error:", err));
            }

            const assistantMsg: Message = {
                id: assistantId,
                role: "assistant",
                content: "",
                agent_name: targetAgent.name,
                agent_avatar: targetAgent.avatar,
                timestamp: Date.now(),
            };
            setMessages((prev) => [...prev, assistantMsg]);

            const response = await fetch(
                "http://localhost:8000/api/chat/stream",
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        agent_id: targetAgent.identifier,
                        content: userMsg.content,
                    }),
                }
            );
            if (!response.ok) throw new Error("网络请求失败");

            const reader = response.body?.getReader();
            if (!reader) throw new Error("流读取器不可用");

            const decoder = new TextDecoder();
            let buffer = "";
            let currentAssistantId = assistantId;
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
                                                    if (
                                                        event.agent_id &&
                                                        event.agent_id !== lastAgentId
                                                    ) {
                                                        // Agent Handoff (Traditional)
                                                        updateWorkflow(lastAgentId, "Idle");
                                                        lastAgentId = event.agent_id;
                                                        updateWorkflow(lastAgentId, "Responding");
                        
                                                        currentAssistantId = (
                                                            Date.now() + Math.random()
                                                        ).toString();
                                                        const newAgent = agentsRef.current.find(
                                                            (a) => a.identifier === event.agent_id
                                                        );
                                                        setMessages((prev) => [
                                                            ...prev,
                                                            {
                                                                id: currentAssistantId,
                                                                role: "assistant",
                                                                content: event.content,
                                                                agent_id: event.agent_id,
                                                                agent_name:
                                                                    newAgent?.name || event.agent_id,
                                                                agent_avatar: newAgent?.avatar || "",
                                                                timestamp: Date.now(),
                                                            },
                                                        ]);
                                                    } else {
                                                        updateWorkflow(lastAgentId, "Responding");
                        
                                                        setMessages((prev) =>
                                                            prev.map((msg) =>
                                                                msg.id === currentAssistantId
                                                                    ? {
                                                                          ...msg,
                                                                          content:
                                                                              (msg.content || "") +
                                                                              event.content,
                                                                      }
                                                                    : msg
                                                            )
                                                        );
                                                    }
                                                } else if (event.type === "status") {
                                                    // Update workflow status for specific agent
                                                    const targetAgentId = event.agent || lastAgentId;
                                                    let status: WorkflowStep["status"] = "Responding";
                                                    if (event.content.includes("正在运行") || event.content.includes("思考")) {
                                                        status = "Thinking";
                                                    }
                                                    updateWorkflow(targetAgentId, status);
                        
                                                    setMessages((prev) =>
                                                        prev.map((msg) =>
                                                            msg.id === currentAssistantId
                                                                ? { ...msg, status: event.content }
                                                                : msg
                                                        )
                                                    );
                                                } else if (event.type === "workflow") {
                                                    if (event.event === "node_added") {
                                                        updateWorkflow(
                                                            event.node.agent_id,
                                                            "Idle",
                                                            event.node.parent_id
                                                        );
                                                    }
                                                }
                    } catch {
                        // Ignore JSON parse errors in stream
                    }
                }
            }
            updateWorkflow(lastAgentId, "Idle");
        } catch (error) {
            console.error("Stream error:", error);
            setMessages((prev) =>
                prev.map((msg) =>
                    msg.id === assistantId
                        ? { ...msg, content: "系统异常，请稍后再试。" }
                        : msg
                )
            );
        } finally {
            setIsLoading(false);
        }
    };

    const scrollToBottom = useCallback(
        (behavior: ScrollBehavior = "smooth") => {
            if (viewportRef.current) {
                isProgrammaticScroll.current = true;
                viewportRef.current.scrollTo({
                    top: viewportRef.current.scrollHeight,
                    behavior,
                });
                setTimeout(() => {
                    isProgrammaticScroll.current = false;
                }, 500);
            }
        },
        []
    );

    const handleScroll = (event: React.UIEvent<HTMLDivElement>) => {
        if (isProgrammaticScroll.current) return;
        const target = event.currentTarget;
        const distanceToBottom =
            target.scrollHeight - target.scrollTop - target.clientHeight;
        const atBottom = distanceToBottom < 20;
        setShowScrollButton(distanceToBottom > 100);
        if (atBottom) setHasNewMessages(false);
    };

    const handleMouseDown = (e: React.MouseEvent) => {
        const startX = e.clientX;
        const startWidth = flowWidth;
        const handleMouseMove = (moveEvent: MouseEvent) => {
            const newWidth = startWidth + (moveEvent.clientX - startX);
            if (newWidth > 320 && newWidth < 800) setFlowWidth(newWidth);
        };
        const handleMouseUp = () => {
            document.removeEventListener("mousemove", handleMouseMove);
            document.removeEventListener("mouseup", handleMouseUp);
        };
        document.addEventListener("mousemove", handleMouseMove);
        document.addEventListener("mouseup", handleMouseUp);
    };

    return (
        <div className="flex h-screen bg-background text-foreground overflow-hidden font-sans relative">
            <HistorySidebar
                isSidebarOpen={isSidebarOpen}
                setIsSidebarOpen={setIsSidebarOpen}
                sessions={sessions}
                currentSessionId={currentSessionId}
                onNewChat={() => {
                    setMessages([]);
                    setCurrentSessionId(null);
                    setSessionTitle("新会话");
                    setWorkflowSteps([]);
                }}
                onSelectSession={(session) => {
                    setCurrentSessionId(session.id);
                    setSessionTitle(session.title);
                    fetchMessages(session.id);
                }}
                onDeleteSession={handleDeleteSession}
            />

            <section
                style={{ width: isFlowOpen ? `${flowWidth}px` : "0px" }}
                className={`flex flex-col z-40 shrink-0 bg-background relative h-full overflow-hidden ${
                    isFlowOpen ? "border-r border-border/40" : ""
                }`}
            >
                {isFlowOpen && (
                    <div
                        className="absolute -right-1 top-0 w-2 h-full cursor-col-resize z-50 hover:bg-primary/30"
                        onMouseDown={handleMouseDown}
                    />
                )}
                <header className="h-12 border-b border-border/40 flex items-center justify-between px-4 shrink-0 bg-background/50 backdrop-blur-md">
                    <div className="flex items-center gap-2">
                        {!isSidebarOpen && (
                            <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => setIsSidebarOpen(true)}
                                className="h-8 w-8"
                            >
                                <PanelLeft size={16} className="rotate-180" />
                            </Button>
                        )}
                        <input
                            value={sessionTitle}
                            onChange={(e) => setSessionTitle(e.target.value)}
                            onBlur={handleUpdateSessionTitle}
                            onKeyDown={(e) =>
                                e.key === "Enter" && handleUpdateSessionTitle()
                            }
                            className="bg-transparent border-none text-[13px] font-bold outline-none flex-1"
                        />
                    </div>
                </header>

                <MessageList
                    messages={messages}
                    isLoading={isLoading}
                    viewportRef={viewportRef}
                    onScroll={handleScroll}
                    showScrollButton={showScrollButton}
                    hasNewMessages={hasNewMessages}
                    onScrollToBottom={() => scrollToBottom("smooth")}
                />

                <ChatInput
                    inputValue={inputValue}
                    setInputValue={setInputValue}
                    isLoading={isLoading}
                    onSend={handleSend}
                    agents={agents}
                />
            </section>

            <div className="flex-1 flex flex-col min-w-0 bg-background relative h-full">
                <header className="h-12 border-b border-border/40 flex items-center justify-between px-6 shrink-0 sticky top-0 z-20 bg-background">
                    <div className="flex items-center gap-4">
                        {!isFlowOpen && (
                            <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => setIsFlowOpen(true)}
                                className="h-8 w-8"
                            >
                                <PanelLeft size={16} className="rotate-180" />
                            </Button>
                        )}
                        <div className="text-[11px] font-bold opacity-50">
                            控制台 / 执行面板
                        </div>
                    </div>
                    <div className="flex -space-x-2">
                        <TooltipProvider>
                            {agents.map((a) => (
                                <Tooltip key={a.id}>
                                    <TooltipTrigger asChild>
                                        <div className="relative group">
                                            <Avatar className="w-7 h-7 border-2 border-background ring-1 ring-border/50">
                                                <AvatarImage src={a.avatar} />
                                                <AvatarFallback className="text-[10px]">
                                                    {a.name.charAt(0)}
                                                </AvatarFallback>
                                            </Avatar>
                                        </div>
                                    </TooltipTrigger>
                                    <TooltipContent
                                        side="bottom"
                                        className="text-xs font-bold p-2"
                                    >
                                        {a.name} - {a.role}
                                    </TooltipContent>
                                </Tooltip>
                            ))}
                        </TooltipProvider>
                    </div>
                </header>
                <main className="flex-1 p-6 relative overflow-hidden">
                    <div className="h-full bg-card rounded-2xl border border-border/40 relative overflow-hidden flex flex-col">
                        {workflowSteps.length > 0 ? (
                            <ExecutionWorkflow workflowSteps={workflowSteps} />
                        ) : (
                            <ExecutionWorkflowEmpty />
                        )}
                    </div>
                </main>
            </div>
        </div>
    );
}
