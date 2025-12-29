"use client";

import { supabase } from "@/lib/supabase";
import {
    Avatar,
    AvatarFallback,
    AvatarImage,
} from "@autonomy/ui/components/avatar";
import { Badge } from "@autonomy/ui/components/badge";
import { Button } from "@autonomy/ui/components/button";
import { Card } from "@autonomy/ui/components/card";
import { ScrollArea } from "@autonomy/ui/components/scroll-area";
import { Separator } from "@autonomy/ui/components/separator";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@autonomy/ui/components/tooltip";
import {
    AtSign,
    Clock,
    Command,
    Globe,
    LayoutGrid,
    MessageSquare,
    PanelLeft,
    Paperclip,
    Plus,
    Send,
    Settings,
    Sparkles,
    StopCircle,
    Zap,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";

interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    agent_id?: string;
    agent_name?: string;
    agent_avatar?: string;
    steps?: number;
    timestamp: number;
}

interface Agent {
    id: string;
    identifier: string;
    name: string;
    role: string;
    avatar: string;
}

interface Report {
    title: string;
    product: string;
    status: string;
    timestamp: string;
    details: string;
}

export default function ExecutionConsole() {
    const [agents, setAgents] = useState<Agent[]>([]);
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputValue, setInputValue] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [activeReport, setActiveReport] = useState<Report | null>(null);
    const [sessionTitle, setSessionTitle] = useState("新会话");
    const [showAgentMenu, setShowAgentMenu] = useState(false);
    const [mentionQuery, setMentionQuery] = useState("");
    const [selectedIndex, setSelectedIndex] = useState(0);
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [isFlowOpen, setIsFlowOpen] = useState(true);
    const scrollRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const filteredAgents = agents.filter((a) =>
        a.name.toLowerCase().includes(mentionQuery.toLowerCase())
    );

    useEffect(() => {
        setSelectedIndex(0);
    }, [mentionQuery]);

    const selectAgent = (agent: Agent) => {
        const textarea = textareaRef.current;
        const cursorPosition = textarea?.selectionStart || inputValue.length;
        const textBeforeCursor = inputValue.substring(0, cursorPosition);
        const lastAtSymbol = textBeforeCursor.lastIndexOf("@");
        const prefix = inputValue.substring(0, lastAtSymbol);
        const suffix = inputValue.substring(cursorPosition);
        
        setInputValue(`${prefix}@${agent.name} ${suffix}`);
        setShowAgentMenu(false);
        setMentionQuery("");
        setSelectedIndex(0);
        
        // Refocus textarea
        setTimeout(() => {
            textarea?.focus();
        }, 0);
    };

    useEffect(() => {
        const fetchAgents = async () => {
            const { data } = await supabase
                .from("agents")
                .select("*")
                .order("identifier");
            if (data) setAgents(data);
        };
        fetchAgents();
    }, []);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, isLoading]);

    const handleSend = async () => {
        if (!inputValue.trim() || isLoading) return;

        const userMsg: Message = {
            id: Date.now().toString(),
            role: "user",
            content: inputValue,
            timestamp: Date.now(),
        };

        setMessages((prev) => [...prev, userMsg]);
        setInputValue("");
        setIsLoading(true);
        setShowAgentMenu(false);

        setTimeout(() => {
            const mentionedAgent = agents.find((a) =>
                userMsg.content.includes(`@${a.name}`)
            );
            const target = mentionedAgent || null;

            const assistantMsg: Message = {
                id: (Date.now() + 1).toString(),
                role: "assistant",
                content: target
                    ? `我是 ${target.name}，已接入全域数据流。正在针对指令进行跨职能建模与逻辑推理...`
                    : "系统调度协议已启动。正在自动匹配职能智能体矩阵进行任务拆解与协同处理。",
                agent_name: target?.name || "System",
                agent_avatar: target?.avatar || "",
                steps: 4,
                timestamp: Date.now(),
            };
            setMessages((prev) => [...prev, assistantMsg]);
            setIsLoading(false);

            setActiveReport({
                title: "全域策略执行报告",
                product: "智能降噪穿戴设备",
                status: "Completed",
                timestamp: new Date().toLocaleTimeString(),
                details:
                    "基于 Autonomy 智能体矩阵的多维分析，该业务目标具备高度可行性。建议立即启动跨职能协同流。",
            });
        }, 1500);
    };

    const startNewSession = () => {
        setMessages([]);
        setActiveReport(null);
        setSessionTitle("新会话");
    };

    return (
        <div className="flex h-screen bg-background text-foreground overflow-hidden font-sans selection:bg-primary/30 relative">
            <div
                className="absolute inset-0 opacity-[0.03] dark:opacity-[0.05] pointer-events-none"
                style={{
                    backgroundImage:
                        "radial-gradient(circle, currentColor 1px, transparent 1px)",
                    backgroundSize: "32px 32px",
                }}
            ></div>

            {/* === 1. History Panel (Sidebar) === */}
            <aside
                className={`flex flex-col z-50 shrink-0 transition-all duration-300 ease-in-out overflow-hidden bg-sidebar relative ${
                    isSidebarOpen
                        ? "w-[240px] border-r border-sidebar-border/40"
                        : "w-0 border-none"
                }`}
            >
                <div className="w-[240px] flex flex-col h-full">
                    {/* Header: Align with h-12 */}
                    <header className="h-12 flex items-center justify-between px-4 shrink-0">
                        <div className="flex items-center gap-2">
                            <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-primary-foreground font-black text-xl shadow-none">
                                A
                            </div>
                            <span className="font-black tracking-tighter text-foreground text-sm uppercase">
                                Autonomy
                            </span>
                        </div>
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setIsSidebarOpen(false)}
                            className="h-8 w-8 text-sidebar-foreground/40 hover:text-background"
                        >
                            <PanelLeft size={16} />
                        </Button>
                    </header>

                    <div className="p-4 pt-6 flex-1 flex flex-col">
                        <div className="mb-4">
                            <Button
                                onClick={startNewSession}
                                className="w-full justify-start gap-3 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 shadow-none rounded-xl h-11 text-xs font-bold transition-all px-4"
                            >
                                <Plus size={18} />
                                开启新会话
                            </Button>
                        </div>

                        <ScrollArea className="flex-1 -mx-2 px-2">
                            <div className="space-y-1.5">
                                <div className="px-4 py-2 text-[10px] font-black text-sidebar-foreground/30 uppercase tracking-[0.2em] mb-1">
                                    最近会话
                                </div>
                                <button className="w-full text-left p-3.5 px-4 rounded-xl bg-primary/10 border border-primary/20 text-xs font-semibold text-primary flex items-center gap-3 group transition-all ring-1 ring-primary/5">
                                    <MessageSquare
                                        size={14}
                                        className="text-primary/70"
                                    />
                                    <span className="truncate flex-1">
                                        {sessionTitle}
                                    </span>
                                    <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                                </button>
                                <button className="w-full text-left p-3.5 px-4 rounded-xl hover:bg-sidebar-accent hover:text-foreground text-xs font-semibold text-sidebar-foreground/50 flex items-center gap-3 group transition-all border border-transparent">
                                    <Clock
                                        size={14}
                                        className="text-sidebar-foreground/30"
                                    />
                                    <span className="truncate">
                                        历史分析报告 12/28
                                    </span>
                                </button>
                            </div>
                        </ScrollArea>
                    </div>

                    <div className="p-4 flex flex-col gap-1 border-t border-sidebar-border/50 bg-sidebar">
                        <Button
                            variant="ghost"
                            className="w-full justify-start gap-3 text-sidebar-foreground/40 hover:text-foreground hover:bg-sidebar-accent rounded-xl text-sm font-semibold px-4 py-3 h-auto transition-all group"
                        >
                            <LayoutGrid
                                size={16}
                                className="text-sidebar-foreground/30 transition-colors"
                            />
                            插件中心
                        </Button>
                        <Button
                            variant="ghost"
                            className="w-full justify-start gap-3 text-sidebar-foreground/40 hover:text-foreground hover:bg-sidebar-accent rounded-xl text-sm font-semibold px-4 py-3 h-auto transition-all group"
                        >
                            <Settings
                                size={16}
                                className="text-sidebar-foreground/30 group-hover:rotate-90 transition-transform duration-500"
                            />
                            系统设置
                        </Button>
                    </div>
                </div>
            </aside>

            {/* === 2. Current Session Panel === */}
            <section
                className={`flex flex-col z-40 shrink-0 transition-all duration-300 ease-in-out overflow-hidden bg-background relative ${
                    isFlowOpen ? "w-[380px]" : "w-0 border-none"
                }`}
            >
                <div className="w-[380px] flex flex-col h-full border-r border-border/40">
                    <header className="h-12 border-b border-border/40 flex items-center justify-between px-4 shrink-0 bg-background/50 backdrop-blur-md">
                        <div className="flex items-center gap-2">
                            {!isSidebarOpen && (
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    onClick={() => setIsSidebarOpen(true)}
                                    className="h-8 w-8 text-muted-foreground hover:text-primary"
                                >
                                    <PanelLeft
                                        size={16}
                                        className="rotate-180"
                                    />
                                </Button>
                            )}
                            <input
                                value={sessionTitle}
                                onChange={(e) => setSessionTitle(e.target.value)}
                                className="bg-transparent border-none focus:ring-0 p-0 text-[13px] font-bold text-foreground/70 ml-1 focus:outline-none flex-1 min-w-0"
                                placeholder="输入会话标题..."
                            />
                        </div>
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setIsFlowOpen(false)}
                            className="h-8 w-8 text-muted-foreground hover:text-background"
                        >
                            <PanelLeft size={16} />
                        </Button>
                    </header>

                    <ScrollArea className="flex-1 bg-muted/5">
                        <div className="p-6 space-y-8 pb-12">
                            {messages.length === 0 && (
                                <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-1000">
                                    <div className="space-y-4 text-primary">
                                        <div className="flex items-center gap-3">
                                            <Sparkles
                                                size={20}
                                                className="fill-primary/20"
                                            />
                                            <h3 className="text-sm font-bold tracking-tight text-primary/80 uppercase">
                                                新会话已就绪
                                            </h3>
                                        </div>
                                        <p className="text-xs font-medium text-muted-foreground leading-relaxed">
                                            智能体矩阵已准备就绪。请输入您的指令以启动全域策略分析或任务调度。
                                        </p>
                                    </div>

                                    <div className="flex flex-col gap-2">
                                        <div className="flex items-center gap-2 px-1 mb-1 opacity-50">
                                            <Command size={10} />
                                            <p className="text-[9px] font-black uppercase tracking-[0.2em]">
                                                快捷指令
                                            </p>
                                        </div>
                                        {[
                                            "分析 24 小时内全平台选品趋势",
                                            "评估供应链稳定性",
                                            "生成 Q1 运营提案",
                                        ].map((tip) => (
                                            <button
                                                key={tip}
                                                onClick={() =>
                                                    setInputValue(tip)
                                                }
                                                className="text-left p-3.5 rounded-xl border border-border bg-background/50 hover:border-primary/40 hover:bg-primary/5 transition-all text-xs font-semibold text-muted-foreground hover:text-foreground group flex items-center justify-between shadow-none"
                                            >
                                                {tip}
                                                <Plus
                                                    size={12}
                                                    className="opacity-0 group-hover:opacity-100 transition-opacity text-primary"
                                                />
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {messages.map((msg) => (
                                <div
                                    key={msg.id}
                                    className="space-y-4 animate-in fade-in duration-500"
                                >
                                    {msg.role === "assistant" ? (
                                        <div className="space-y-3">
                                            <div className="flex items-center gap-2.5">
                                                <div className="w-6 h-6 rounded-md bg-primary/10 overflow-hidden ring-1 ring-primary/20 flex items-center justify-center">
                                                    {msg.agent_avatar ? (
                                                        <img
                                                            src={
                                                                msg.agent_avatar
                                                            }
                                                            alt={msg.agent_name}
                                                            className="w-full h-full object-cover"
                                                        />
                                                    ) : (
                                                        <span className="text-[10px] font-bold">
                                                            {msg.agent_name?.charAt(
                                                                0
                                                            )}
                                                        </span>
                                                    )}
                                                </div>
                                                <span className="text-[11px] font-bold uppercase text-foreground/80 tracking-widest">
                                                    {msg.agent_name}
                                                </span>
                                            </div>
                                            <div className="text-sm leading-relaxed text-foreground/90 pl-8.5 font-medium border-l-2 border-primary/10 ml-3">
                                                {msg.content}
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="flex flex-col items-end">
                                            <div className="bg-primary/5 border border-primary/20 p-4 rounded-2xl rounded-tr-none text-sm font-semibold max-w-[90%] text-primary leading-relaxed shadow-none">
                                                {msg.content}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </ScrollArea>

                    <div className="p-6 bg-background relative">
                        {showAgentMenu && (
                            <Card className="absolute bottom-full left-6 w-56 gap-0 bg-popover/95 backdrop-blur-2xl border-border shadow-2xl p-1 z-50 rounded-xl ring-1 ring-border animate-in slide-in-from-bottom-2">
                                <div className="px-2 py-1.5 text-[10px] font-black text-muted-foreground uppercase tracking-widest border-b border-border/50 mb-1">
                                    智能体
                                </div>
                                <div className="max-h-48 overflow-y-auto scrollbar-hide">
                                    {filteredAgents.map((agent, index) => (
                                        <button
                                            key={agent.id}
                                            onClick={() => selectAgent(agent)}
                                            className={`w-full flex items-center gap-2.5 p-1.5 rounded-lg transition-all text-left group ${
                                                index === selectedIndex
                                                    ? "bg-primary/20 ring-1 ring-primary/30"
                                                    : "hover:bg-primary/10"
                                            }`}
                                        >
                                            <div className="w-6 h-6 rounded-md bg-muted overflow-hidden ring-1 ring-border/50 group-hover:ring-primary/30 shrink-0">
                                                <img
                                                    src={agent.avatar}
                                                    alt={agent.name}
                                                    className="w-full h-full object-cover"
                                                />
                                            </div>
                                            <div className={`text-[11px] font-bold transition-colors truncate ${
                                                index === selectedIndex ? "text-primary" : "group-hover:text-primary"
                                            }`}>
                                                {agent.name}
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            </Card>
                        )}
                        <Card className="bg-background/50 border-border/40 shadow-none rounded-xl p-1.5 flex flex-col gap-1 transition-all overflow-hidden group-focus-within:ring-1 group-focus-within:ring-primary/30">
                            <textarea
                                ref={textareaRef}
                                value={inputValue}
                                onChange={(e) => {
                                    const val = e.target.value;
                                    setInputValue(val);

                                    const cursorPosition =
                                        e.target.selectionStart;
                                    const textBeforeCursor = val.substring(
                                        0,
                                        cursorPosition
                                    );
                                    const lastAtSymbol =
                                        textBeforeCursor.lastIndexOf("@");

                                    if (lastAtSymbol !== -1) {
                                        const charBeforeAt =
                                            lastAtSymbol > 0
                                                ? textBeforeCursor[
                                                      lastAtSymbol - 1
                                                  ]
                                                : "";
                                        const query =
                                            textBeforeCursor.substring(
                                                lastAtSymbol + 1
                                            );

                                        // Only trigger if @ is at start or preceded by space/newline, and no space in query
                                        if (
                                            (lastAtSymbol === 0 ||
                                                charBeforeAt === " " ||
                                                charBeforeAt === "\n") &&
                                            !query.includes(" ")
                                        ) {
                                            setShowAgentMenu(true);
                                            setMentionQuery(query);
                                        } else {
                                            setShowAgentMenu(false);
                                            setMentionQuery("");
                                        }
                                    } else {
                                        setShowAgentMenu(false);
                                        setMentionQuery("");
                                    }
                                }}
                                onKeyDown={(e) => {
                                    if (showAgentMenu && filteredAgents.length > 0) {
                                        if (e.key === "ArrowDown") {
                                            e.preventDefault();
                                            setSelectedIndex((prev) => (prev + 1) % filteredAgents.length);
                                            return;
                                        }
                                        if (e.key === "ArrowUp") {
                                            e.preventDefault();
                                            setSelectedIndex((prev) => (prev - 1 + filteredAgents.length) % filteredAgents.length);
                                            return;
                                        }
                                        if (e.key === "Enter") {
                                            e.preventDefault();
                                            selectAgent(filteredAgents[selectedIndex]);
                                            return;
                                        }
                                        if (e.key === "Escape") {
                                            e.preventDefault();
                                            setShowAgentMenu(false);
                                            return;
                                        }
                                    }

                                    if (e.key === "Enter" && !e.shiftKey) {
                                        e.preventDefault();
                                        handleSend();
                                    }
                                }}
                                placeholder="输入指令或使用 @ 呼叫智能体..."
                                className="w-full bg-transparent border-none focus:ring-0 p-3 text-sm font-medium resize-none min-h-[90px] outline-none placeholder:text-muted-foreground/30 leading-relaxed"
                            />
                            <div className="flex items-center justify-between px-2 pb-1.5">
                                <div className="flex items-center gap-1">
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        className="h-8 w-8 rounded-lg text-muted-foreground hover:text-primary hover:bg-primary/10 transition-colors"
                                    >
                                        <Paperclip size={16} />
                                    </Button>
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        className="h-8 w-8 rounded-lg text-muted-foreground hover:text-primary hover:bg-primary/10 transition-colors"
                                        onClick={() =>
                                            setShowAgentMenu(!showAgentMenu)
                                        }
                                    >
                                        <AtSign size={16} />
                                    </Button>
                                </div>
                                <Button
                                    size="icon"
                                    disabled={!inputValue.trim() || isLoading}
                                    onClick={handleSend}
                                    className="h-9 w-9 rounded-full bg-primary text-primary-foreground shadow-lg shadow-primary/20 hover:scale-105 active:scale-95 transition-all"
                                >
                                    {isLoading ? (
                                        <StopCircle
                                            size={16}
                                            className="animate-spin"
                                        />
                                    ) : (
                                        <Send size={16} />
                                    )}
                                </Button>
                            </div>
                        </Card>
                    </div>
                </div>
            </section>

            {/* === 3. Main Display Panel === */}
            <div className="flex-1 flex flex-col min-w-0 relative h-full bg-background">
                <header className="h-12 border-b border-border/40 bg-background flex items-center justify-between px-6 shrink-0 sticky top-0 z-20">
                    <div className="flex items-center gap-4">
                        {!isFlowOpen && (
                            <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => setIsFlowOpen(true)}
                                className="h-8 w-8 text-muted-foreground hover:text-primary bg-primary/5 transition-colors"
                            >
                                <PanelLeft size={16} className="rotate-180" />
                            </Button>
                        )}
                        <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-widest text-muted-foreground/50">
                            <span>控制台</span>
                            <span className="text-border">/</span>
                            <span className="text-foreground/70">执行面板</span>
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="flex -space-x-2">
                            <TooltipProvider>
                                {agents.map((agent) => (
                                    <Tooltip key={agent.id}>
                                        <TooltipTrigger asChild>
                                            <Avatar className="w-7 h-7 border-2 border-background shadow-none ring-1 ring-border/50 cursor-help">
                                                <AvatarImage
                                                    src={agent.avatar}
                                                    alt={agent.name}
                                                />
                                                <AvatarFallback className="text-[10px] bg-muted">
                                                    {agent.name.charAt(0)}
                                                </AvatarFallback>
                                            </Avatar>
                                        </TooltipTrigger>
                                        <TooltipContent
                                            side="bottom"
                                            className="flex flex-row items-center gap-2.5 py-1.5 px-3"
                                        >
                                            <span className="font-bold text-xs">
                                                {agent.name}
                                            </span>
                                            <span className="text-[10px] font-black uppercase tracking-widest text-primary bg-primary/10 px-1.5 py-0.5 rounded-md border border-primary/20">
                                                {agent.role}
                                            </span>
                                        </TooltipContent>
                                    </Tooltip>
                                ))}
                            </TooltipProvider>
                        </div>
                    </div>
                </header>

                <main className="flex-1 flex flex-col relative overflow-hidden">
                    <div className="flex-1 flex flex-col bg-card rounded-2xl border border-border/40 shadow-none m-6 overflow-hidden relative animate-in fade-in zoom-in-95 duration-500">
                        <div className="flex-1 h-0 overflow-y-auto bg-background scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent">
                            <div className="p-12 max-w-5xl mx-auto min-h-full flex flex-col">
                                {activeReport ? (
                                    <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 space-y-12 pb-12">
                                        <div className="flex items-end justify-between border-b border-border pb-10">
                                            <div className="space-y-5">
                                                <Badge className="bg-primary/10 text-primary border-primary/20 font-black text-[10px] px-3.5 py-1 uppercase tracking-[0.2em]">
                                                    {activeReport.status}
                                                </Badge>
                                                <h2 className="text-5xl font-black tracking-tighter italic leading-none text-foreground">
                                                    {activeReport.title}
                                                </h2>
                                                <div className="flex items-center gap-5 text-muted-foreground">
                                                    <div className="flex items-center gap-2">
                                                        <Globe
                                                            size={14}
                                                            className="text-primary/60"
                                                        />
                                                        <span className="text-[11px] font-bold uppercase tracking-widest">
                                                            {
                                                                activeReport.product
                                                            }
                                                        </span>
                                                    </div>
                                                    <Separator
                                                        orientation="vertical"
                                                        className="h-4 opacity-50"
                                                    />
                                                    <span className="text-[11px] font-mono opacity-50 uppercase tracking-widest">
                                                        {activeReport.timestamp}
                                                    </span>
                                                </div>
                                            </div>
                                            <div className="w-16 h-16 bg-primary/5 border border-primary/10 rounded-2xl flex items-center justify-center text-primary/40 shadow-inner">
                                                <Zap size={32} />
                                            </div>
                                        </div>

                                        <Card className="overflow-hidden border-border/60 shadow-none rounded-[24px] bg-card">
                                            <div className="aspect-21/9 bg-muted overflow-hidden relative border-b border-border/50">
                                                <img
                                                    src="https://images.unsplash.com/photo-1541506618330-7c369fc759b5?q=80&w=1000&auto=format&fit=crop"
                                                    alt="Strategic Analysis"
                                                    className="w-full h-full object-cover saturate-50 hover:saturate-100 transition-all duration-1000"
                                                />
                                                <div className="absolute inset-0 bg-linear-to-t from-card via-transparent to-transparent opacity-60" />
                                                <div className="absolute bottom-8 left-10">
                                                    <Badge className="bg-green-600 text-white border-none font-black text-[10px] px-4 py-1.5 tracking-widest uppercase">
                                                        分析结果已就绪
                                                    </Badge>
                                                </div>
                                            </div>
                                            <div className="p-10 space-y-12">
                                                <div className="grid grid-cols-3 gap-10 text-center">
                                                    <div className="space-y-3">
                                                        <span className="text-[10px] font-black text-muted-foreground/60 uppercase tracking-[0.3em]">
                                                            预估回报
                                                        </span>
                                                        <div className="text-4xl font-black text-primary tracking-tighter">
                                                            35.2%
                                                        </div>
                                                    </div>
                                                    <div className="space-y-3 border-l border-border/50 pl-10">
                                                        <span className="text-[10px] font-black text-muted-foreground/60 uppercase tracking-[0.3em]">
                                                            置信度
                                                        </span>
                                                        <div className="text-4xl font-black tracking-tighter text-foreground">
                                                            0.94
                                                        </div>
                                                    </div>
                                                    <div className="space-y-3 border-l border-border/50 pl-10">
                                                        <span className="text-[10px] font-black text-muted-foreground/60 uppercase tracking-[0.3em]">
                                                            风险模型
                                                        </span>
                                                        <div className="text-4xl font-black text-orange-500 tracking-tighter uppercase">
                                                            Low
                                                        </div>
                                                    </div>
                                                </div>
                                                <Separator className="opacity-50" />
                                                <div className="space-y-6">
                                                    <div className="flex items-center gap-3">
                                                        <div className="w-2 h-5 bg-primary rounded-full" />
                                                        <h4 className="text-xs font-black uppercase tracking-[0.3em] text-foreground/80">
                                                            策略分析摘要
                                                        </h4>
                                                    </div>
                                                    <p className="text-sm leading-relaxed text-muted-foreground font-medium bg-muted/10 p-8 rounded-2xl border border-border/40 border-dashed">
                                                        {activeReport.details}{" "}
                                                        本次分析已同步检索全球
                                                        48
                                                        个主要市场的实时波动数据。建议立即锁定相关资源并启动跨境协同流。
                                                    </p>
                                                </div>
                                            </div>
                                        </Card>
                                    </div>
                                ) : (
                                    <div className="flex-1 flex flex-col items-center justify-center text-center space-y-12 opacity-30 grayscale mix-blend-luminosity min-h-[400px]">
                                        <div className="relative">
                                            <div className="absolute inset-0 bg-primary/10 blur-[120px] rounded-full scale-150" />
                                            <div className="w-32 h-32 relative border border-primary/10 bg-card flex items-center justify-center rounded-[48px] shadow-sm">
                                                <Zap
                                                    size={64}
                                                    className="text-primary/40 animate-pulse"
                                                />
                                            </div>
                                        </div>
                                        <div className="space-y-5">
                                            <h3 className="text-4xl font-black uppercase tracking-[0.5em] italic text-muted-foreground/20">
                                                待机中
                                            </h3>
                                            <div className="flex items-center justify-center gap-4 text-xs font-black text-muted-foreground/40 uppercase tracking-[0.3em]">
                                                等待矩阵指令流
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </main>
            </div>
        </div>
    );
}
