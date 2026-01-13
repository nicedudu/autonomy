"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Loader2, PanelLeft } from "lucide-react";
import { useNodesState, useEdgesState } from "@xyflow/react";

import { Avatar, AvatarFallback, AvatarImage } from "@autonomy/ui/components/avatar";
import { Button } from "@autonomy/ui/components/button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@autonomy/ui/components/tooltip";

import { HistorySidebar } from "@/features/sessions/components/history-sidebar";
import { useSessions } from "@/features/sessions/hooks/use-sessions";
import { MessageList } from "@/features/chat/components/message-list";
import { ChatInput } from "@/features/chat/components/chat-input";
import { useChat } from "@/features/chat/hooks/use-chat";
import { WorkflowGraph } from "@/features/execution/components/workflow-graph";
import { useAgentControl } from "@/features/execution/hooks/use-agent-control";
import { ExecutionWorkflowEmpty } from "@/features/execution/components/execution-workflow-empty";
import { ENDPOINTS } from "@/lib/api";

interface Agent {
    id: string;
    identifier: string;
    name: string;
    role: string;
    avatar: string;
}

export default function ExecutionConsole() {
    // 1. Hooks
    const { 
        sessions, currentSessionId, setCurrentSessionId, 
        sessionTitle, setSessionTitle, createSession, 
        updateSessionTitle, deleteSession 
    } = useSessions();

    const { messages, setMessages, isLoading, sendMessage, fetchMessages } = useChat(currentSessionId);
    const { nodes: graphNodes, edges: graphEdges, status: wsStatus } = useAgentControl(currentSessionId);

    // 2. UI State
    const [agents, setAgents] = useState<Agent[]>([]);
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [isFlowOpen, setIsFlowOpen] = useState(true);
    const [flowWidth, setFlowWidth] = useState(380);
    const [inputValue, setInputValue] = useState("");
    
    const [showScrollButton, setShowScrollButton] = useState(false);
    const [hasNewMessages, setHasNewMessages] = useState(false);

    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);

    const viewportRef = useRef<HTMLDivElement>(null);
    const isProgrammaticScroll = useRef(false);

    // 3. Scroll Logic
    const scrollToBottom = useCallback((behavior: ScrollBehavior = "smooth") => {
        if (viewportRef.current) {
            isProgrammaticScroll.current = true;
            viewportRef.current.scrollTo({ top: viewportRef.current.scrollHeight, behavior });
            setTimeout(() => { isProgrammaticScroll.current = false; }, 500);
        }
    }, []);

    const handleScroll = (event: React.UIEvent<HTMLDivElement>) => {
        if (isProgrammaticScroll.current) return;
        const target = event.currentTarget;
        const dist = target.scrollHeight - target.scrollTop - target.clientHeight;
        setShowScrollButton(dist > 100);
        if (dist < 20) setHasNewMessages(false);
    };

    useEffect(() => {
        if (isLoading && viewportRef.current) {
            const target = viewportRef.current;
            const dist = target.scrollHeight - target.scrollTop - target.clientHeight;
            if (dist < 150) {
                requestAnimationFrame(() => { target.scrollTop = target.scrollHeight; });
            } else {
                setHasNewMessages(true);
            }
        }
    }, [messages, isLoading]);

    // 4. Effects
    useEffect(() => {
        setNodes(graphNodes);
        setEdges(graphEdges);
    }, [graphNodes, graphEdges, setNodes, setEdges]);

    useEffect(() => {
        fetch(ENDPOINTS.AGENTS).then(res => res.ok && res.json()).then(setAgents).catch(console.error);
    }, []);

    // 5. Handlers
    const handleSend = async () => {
        if (!inputValue.trim() || isLoading) return;
        const content = inputValue;
        const isFirst = messages.length === 0;
        let sid = currentSessionId;
        if (!sid) {
            const newS = await createSession();
            if (newS) { sid = newS.id; setCurrentSessionId(sid); }
        }
        if (!sid) return;
        const target = agents.find(a => inputValue.includes(`@${a.name}`)) || agents.find(a => a.identifier === "primary_agent");
        if (!target) return;
        setInputValue("");
        
        if (isFirst) {
            fetch(ENDPOINTS.CHAT_SUMMARIZE, { 
                method: "POST", 
                headers: { "Content-Type": "application/json" }, 
                body: JSON.stringify({ content }) 
            })
            .then(res => res.json())
            .then(data => {
                if (data.title) {
                    setSessionTitle(data.title);
                    updateSessionTitle(sid!, data.title);
                }
            })
            .catch(err => console.error("Summarize failed:", err));
        }
        await sendMessage(content, target, sid);
    };

    const handleSelectSession = (s: any) => {
        if (s.id === currentSessionId) return;
        setCurrentSessionId(s.id);
        setSessionTitle(s.title);
        setHasNewMessages(false);
        fetchMessages(s.id);
        requestAnimationFrame(() => { if (viewportRef.current) viewportRef.current.scrollTop = 0; });
    };

    const handleMouseDown = (e: React.MouseEvent) => {
        const startX = e.clientX;
        const startWidth = flowWidth;
        const handleMouseMove = (mv: MouseEvent) => {
            const newWidth = startWidth + (mv.clientX - startX);
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
                onNewChat={() => { setCurrentSessionId(null); setSessionTitle("新会话"); setMessages([]); setNodes([]); setEdges([]); }}
                onSelectSession={handleSelectSession}
                onDeleteSession={deleteSession}
            />

            {/* 会话面板 */}
            <section
                style={{ width: isFlowOpen ? `${flowWidth}px` : "0px" }}
                className={`flex flex-col z-40 shrink-0 bg-background relative h-full overflow-hidden ${isFlowOpen ? "border-r border-border/40" : ""}`}
            >
                {isFlowOpen && (
                    <div className="absolute -right-1 top-0 w-2 h-full cursor-col-resize z-50 hover:bg-primary/30" onMouseDown={handleMouseDown} />
                )}
                <header className="h-12 border-b border-border/40 flex items-center px-4 shrink-0 bg-background/50 backdrop-blur-md">
                    <div className="flex items-center gap-2 flex-1">
                        {!isSidebarOpen && (
                            <Button variant="ghost" size="icon" onClick={() => setIsSidebarOpen(true)} className="h-8 w-8">
                                <PanelLeft size={16} className="rotate-180" />
                            </Button>
                        )}
                        <input
                            value={sessionTitle}
                            onChange={(e) => setSessionTitle(e.target.value)}
                            onBlur={() => currentSessionId && updateSessionTitle(currentSessionId, sessionTitle)}
                            className="bg-transparent border-none text-[13px] font-bold outline-none flex-1"
                        />
                    </div>
                    {/* [需求还原]: 当面板展开时，折叠按钮在面板右侧 */}
                    <Button variant="ghost" size="icon" onClick={() => setIsFlowOpen(false)} className="h-8 w-8">
                        <PanelLeft size={16} />
                    </Button>
                </header>

                <MessageList messages={messages} isLoading={isLoading} viewportRef={viewportRef} onScroll={handleScroll} showScrollButton={showScrollButton} hasNewMessages={hasNewMessages} onScrollToBottom={() => scrollToBottom("smooth")} />
                <ChatInput inputValue={inputValue} setInputValue={setInputValue} isLoading={isLoading} onSend={handleSend} agents={agents} />
            </section>

            {/* 执行控制面板 */}
            <div className="flex-1 flex flex-col min-w-0 bg-background relative h-full">
                <header className="h-12 border-b border-border/40 flex items-center justify-between px-6 shrink-0 sticky top-0 z-20 bg-background">
                    <div className="flex items-center gap-4">
                        {/* [需求还原]: 仅在面板折叠后，切换按钮才出现在此控制面板 */}
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
                        
                        <div className="flex items-center gap-2">
                            <div className="text-[11px] font-bold opacity-50 uppercase tracking-wider">
                                Control Plane / Live Execution
                            </div>
                            {wsStatus === 'connected' && (
                                <div className="flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-green-50 text-[9px] text-green-600 font-bold border border-green-200">
                                    <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                                    LIVE
                                </div>
                            )}
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
                                                <AvatarFallback className="text-[10px]">{a.name.charAt(0)}</AvatarFallback>
                                            </Avatar>
                                        </div>
                                    </TooltipTrigger>
                                    <TooltipContent side="bottom" className="text-xs font-bold p-2">{a.name} - {a.role}</TooltipContent>
                                </Tooltip>
                            ))}
                        </TooltipProvider>
                    </div>
                </header>
                
                <main className="flex-1 p-6 relative overflow-hidden">
                    <div className="h-full bg-card rounded-2xl border border-border/40 relative overflow-hidden flex flex-col">
                        {nodes.length > 0 ? (
                            <WorkflowGraph nodes={nodes} edges={edges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} />
                        ) : (
                            <ExecutionWorkflowEmpty />
                        )}
                    </div>
                </main>
            </div>
        </div>
    );
}