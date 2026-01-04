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
    Brain,
    ChevronDown,
    ChevronRight,
    Clock,
    Command,
    Globe,
    LayoutGrid,
    Lightbulb,
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
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

// --- Data Visualization Renderer ---
const ChartRenderer = ({ data }: { data: any }) => {
    return (
        <div className="my-6 bg-card border border-border/60 rounded-2xl overflow-hidden shadow-sm animate-in fade-in zoom-in-95 duration-500">
            <div className="bg-muted/30 px-4 py-3 border-b border-border/40 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                    <span className="text-[10px] font-black uppercase tracking-widest text-foreground/70">
                        {data.chartType || "数据可视化"}
                    </span>
                </div>
                <Badge
                    variant="outline"
                    className="text-[9px] font-mono opacity-50 uppercase"
                >
                    Live Data
                </Badge>
            </div>
            <div className="p-6 flex flex-col items-center justify-center min-h-[200px] bg-linear-to-b from-transparent to-primary/5">
                <div className="text-center space-y-2">
                    <p className="text-xs font-bold text-foreground/80">
                        {data.title || "正在渲染图表结构..."}
                    </p>
                    <div className="flex gap-1 justify-center items-end h-12">
                        {[40, 70, 45, 90, 65].map((h, i) => (
                            <div
                                key={i}
                                className="w-2 bg-primary/20 rounded-t-sm animate-in slide-in-from-bottom duration-1000"
                                style={{
                                    height: `${h}%`,
                                    transitionDelay: `${i * 100}ms`,
                                }}
                            />
                        ))}
                    </div>
                    <p className="text-[10px] text-muted-foreground font-medium">
                        数据点: {data.data?.length || 0} 个维度已锁定
                    </p>
                </div>
            </div>
        </div>
    );
};

const MarkdownComponents = {
    p: ({ children }: any) => (
        <p className="mb-3 last:mb-0 leading-relaxed break-all whitespace-pre-wrap min-w-0">
            {children}
        </p>
    ),
    h1: ({ children }: any) => (
        <h1 className="text-xl font-black mb-4 mt-6 text-foreground tracking-tight">
            {children}
        </h1>
    ),
    h2: ({ children }: any) => (
        <h2 className="text-lg font-bold mb-3 mt-5 text-foreground/90 tracking-tight">
            {children}
        </h2>
    ),
    h3: ({ children }: any) => (
        <h3 className="text-base font-bold mb-2 mt-4 text-foreground/80">
            {children}
        </h3>
    ),

    // --- Enhanced Lists ---
    li: ({ children }: any) => (
        <li className="mb-1.5 min-w-0 break-all leading-relaxed">
            {children}
        </li>
    ),
    ul: ({ children }: any) => <ul className="mb-4 space-y-1 list-disc pl-5 marker:text-primary/40">{children}</ul>,
    ol: ({ children }: any) => (
        <ol className="list-decimal pl-5 mb-4 space-y-1.5 marker:text-primary/50 marker:font-mono marker:text-xs">
            {children}
        </ol>
    ),

    // --- Enhanced Blockquote ---
    blockquote: ({ children }: any) => (
        <div className="flex gap-3 bg-linear-to-r from-primary/5 to-transparent p-4 my-4 rounded-xl border border-primary/10 shadow-sm items-start not-prose animate-in slide-in-from-left-2">
            <div className="p-1 bg-primary/10 text-primary rounded-lg shrink-0 mt-0.5">
                <Lightbulb size={16} />
            </div>
            <div className="text-foreground/80 text-sm font-medium italic leading-relaxed">
                {children}
            </div>
        </div>
    ),

    // --- Intelligent Code & Chart Logic ---
    code: (props: any) => {
        const { node, inline, className, children, ...rest } = props;
        const match = /language-(\w+)/.exec(className || "");
        const isJson = match && match[1] === "json";

        if (!inline && isJson) {
            try {
                const jsonStr = String(children).replace(/\n$/, "");
                if (
                    jsonStr.includes("chartType") &&
                    jsonStr.includes("data")
                ) {
                    const data = JSON.parse(jsonStr);
                    if (data.chartType && data.data)
                        return <ChartRenderer data={data} />;
                }
            } catch (e) {}
        }

        return inline ? (
            <code
                className="bg-primary/10 text-primary px-1.5 py-0.5 rounded font-mono text-[0.85em] font-bold"
                {...rest}
            >
                {children}
            </code>
        ) : (
            <div className="relative my-4 group max-w-full">
                <pre className="bg-muted/50 border border-border/40 rounded-xl p-4 overflow-x-auto font-mono text-xs leading-relaxed scrollbar-thin">
                    <code className={className}>{children}</code>
                </pre>
                {match && (
                    <div className="absolute top-2 right-3 text-[10px] font-black uppercase text-muted-foreground/40 pointer-events-none">
                        {match[1]}
                    </div>
                )}
            </div>
        );
    },

    // --- Enhanced Tables ---
    table: ({ children }: any) => (
        <div className="my-6 w-full overflow-hidden rounded-xl border border-border/40 bg-muted/5 not-prose">
            <div className="overflow-x-auto">
                <table className="w-full text-xs text-left border-collapse">
                    {children}
                </table>
            </div>
        </div>
    ),
    thead: ({ children }: any) => (
        <thead className="bg-muted/50 text-muted-foreground font-bold uppercase tracking-wider border-b border-border/40">
            {children}
        </thead>
    ),
    th: ({ children }: any) => (
        <th className="px-4 py-3 whitespace-nowrap">{children}</th>
    ),
    tbody: ({ children }: any) => (
        <tbody className="divide-y divide-border/10">{children}</tbody>
    ),
    tr: ({ children }: any) => (
        <tr className="group transition-colors hover:bg-primary/5">
            {children}
        </tr>
    ),
    td: ({ children }: any) => (
        <td className="px-4 py-3 text-foreground/80 border-none group-first:font-bold group-first:text-foreground">
            {children}
        </td>
    ),

    a: ({ children, href }: any) => (
        <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:underline underline-offset-4 font-bold decoration-primary/30"
        >
            {children}
        </a>
    ),
    strong: ({ children }: any) => {
        const content = String(children);
        if (content.startsWith("@")) {
            return (
                <span className="inline-flex items-center gap-1 text-primary font-bold mx-0.5">
                    <AtSign size={10} strokeWidth={3} />
                    {content.substring(1)}
                </span>
            );
        }
        return (
            <strong className="font-bold text-foreground antialiased">
                {children}
            </strong>
        );
    },
    hr: ({ children }: any) => <hr className="my-6 border-border/20" />,
};

// --- Todo List Renderer ---
const PlanTodoView = ({ content }: { content: string }) => {
    const lines = content.split("\n").filter((line) => line.trim() !== "");

    return (
        <div className="my-4 bg-primary/5 border border-primary/10 rounded-xl overflow-hidden shadow-sm animate-in fade-in slide-in-from-bottom-2">
            <div className="bg-primary/10 px-3 py-2 border-b border-primary/10 flex items-center gap-2">
                <LayoutGrid size={14} className="text-primary" />
                <span className="text-[10px] font-black uppercase tracking-widest text-primary">
                    执行计划 (Action Plan)
                </span>
            </div>
            <div className="p-4 space-y-1.5">
                {lines.map((line, i) => {
                    const indentMatch = line.match(/^(\s*)/);
                    const indentLevel = indentMatch ? Math.floor(indentMatch[0].length / 2) : 0;
                    const trimmedLine = line.trim();
                    const isTodoTask = /^[-*+]\s*\[[\sxX\/]\]/.test(trimmedLine);
                    const isDone = /^[-*+]\s*\[[xX]\]/.test(trimmedLine);
                    const isInProgress = /^[-*+]\s*\[\/\]/.test(trimmedLine);
                    
                    const cleanContent = trimmedLine
                        .replace(/^[-*+]\s*(\[[\sxX\/]\])?\s*/, "")
                        .replace(/^\d+\.\s*/, "")
                        .replace(/<call>\s*(@\w+)\s*(.*?)\s*<\/call>/gs, "**$1** $2")
                        .replace(/<call>\s*(@\w+)?\s*(.*?)$/gs, "**$1** $2");

                    return (
                        <div
                            key={i}
                            className="flex items-start gap-2 group transition-all"
                            style={{ paddingLeft: `${indentLevel * 0.75}rem` }}
                        >
                            {isTodoTask ? (
                                <div className="mt-1 shrink-0">
                                    {isDone ? (
                                        <div className="w-3.5 h-3.5 rounded-full bg-primary flex items-center justify-center shadow-sm">
                                            <div className="w-1.5 h-1.5 bg-white rounded-full" />
                                        </div>
                                    ) : isInProgress ? (
                                        <div className="w-3.5 h-3.5 rounded-full border-2 border-primary flex items-center justify-center animate-pulse">
                                            <div className="w-1.5 h-1.5 bg-primary rounded-full animate-ping" />
                                        </div>
                                    ) : (
                                        <div className="w-3.5 h-3.5 rounded-full border-2 border-primary/30 group-hover:border-primary/50 transition-colors" />
                                    )}
                                </div>
                            ) : (
                                <div className="mt-2 shrink-0 flex justify-center w-3.5">
                                    <div className="w-1 h-1 rounded-full bg-muted-foreground/30" />
                                </div>
                            )}
                            <div
                                className={`text-[13px] font-medium leading-relaxed max-w-none flex-1 ${isDone ? "text-muted-foreground/50 line-through decoration-primary/20" : isInProgress ? "text-primary font-bold" : "text-foreground/80"}`}
                            >
                                <ReactMarkdown 
                                    remarkPlugins={[remarkGfm]}
                                    components={{
                                        p: ({children}) => <span className="block mb-1 last:mb-0">{children}</span>,
                                        strong: ({ children }: any) => {
                                            const content = String(children);
                                            if (content.startsWith("@")) {
                                                return (
                                                    <span className="inline-flex items-center gap-0.5 text-primary font-bold">
                                                        {content}
                                                    </span>
                                                );
                                            }
                                            return <strong className="font-black text-foreground">{children}</strong>;
                                        },
                                        code: ({children}) => <code className="bg-primary/5 px-1 rounded text-primary/70">{children}</code>
                                    }}
                                >
                                    {cleanContent}
                                </ReactMarkdown>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

// --- Assistant Message Component ---
const AssistantMessageItem = ({
    msg,
    isLatest,
    isLoading,
}: {
    msg: Message;
    isLatest: boolean;
    isLoading: boolean;
}) => {
    const [isThinkingExpanded, setIsThinkingExpanded] = useState(false);
    const [isHovered, setIsHovered] = useState(false);

    const content = msg.content || "";

    // Tags Parsing Logic
    const parseAllTags = (startTag: string, endTag: string) => {
        const results = [];
        let cursor = 0;
        while (true) {
            const startIdx = content.indexOf(startTag, cursor);
            if (startIdx === -1) break;
            const endIdx = content.indexOf(endTag, startIdx + startTag.length);
            results.push({
                content: endIdx !== -1 ? content.substring(startIdx + startTag.length, endIdx) : content.substring(startIdx + startTag.length),
                isClosed: endIdx !== -1,
            });
            if (endIdx === -1) break;
            cursor = endIdx + endTag.length;
        }
        return results;
    };

    const allThoughts = parseAllTags("<thought>", "</thought>");
    const allPlans = parseAllTags("<plan>", "</plan>");
    const thought = allThoughts[allThoughts.length - 1] || null;
    const plan = allPlans[allPlans.length - 1] || null;
    const isStreaming = isLatest && isLoading;

    let mainContent = content;
    // Strip blocks that have dedicated UI renderers
    const blocksToHide = [
        { start: "<thought>", end: "</thought>" },
        { start: "<plan>", end: "</plan>" },
        { start: "<action>", end: "</action>" },
        { start: "<status>", end: "</status>" },
    ];

    blocksToHide.forEach((block) => {
        while (true) {
            const s = mainContent.indexOf(block.start);
            if (s === -1) break;
            const e = mainContent.indexOf(block.end, s);
            if (e !== -1) {
                mainContent = mainContent.substring(0, s) + mainContent.substring(e + block.end.length);
            } else {
                mainContent = mainContent.substring(0, s);
                break;
            }
        }
    });

    mainContent = mainContent.replace(/<call>\s*(@\w+)\s*(.*?)\s*<\/call>/gs, "\n\n> **$1** $2\n\n").trim();

    return (
        <div className="space-y-3 w-full min-w-0 overflow-hidden">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                    <div className="w-6 h-6 rounded-md bg-primary/10 overflow-hidden ring-1 ring-primary/20 flex items-center justify-center">
                        {msg.agent_avatar ? (
                            <img src={msg.agent_avatar} alt={msg.agent_name} className="w-full h-full object-cover" />
                        ) : (
                            <span className="text-[10px] font-bold">{msg.agent_name?.charAt(0)}</span>
                        )}
                    </div>
                    <span className="text-[11px] font-bold text-foreground/80 tracking-widest">{msg.agent_name}</span>
                </div>
                {msg.timestamp && (
                    <span className="text-[9px] font-medium text-muted-foreground/50 tabular-nums">
                        {new Date(msg.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </span>
                )}
            </div>

            {thought && (
                <div className={`rounded-xl overflow-hidden transition-all w-full min-w-0 ${isThinkingExpanded ? "bg-muted/30 border border-border/40" : "bg-transparent"}`}>
                    <button onClick={() => setIsThinkingExpanded(!isThinkingExpanded)} onMouseEnter={() => setIsHovered(true)} onMouseLeave={() => setIsHovered(false)} className="flex items-center gap-2 px-1.5 py-1.5 hover:text-foreground/80 transition-colors text-[10px] font-bold text-muted-foreground/70 uppercase tracking-tight">
                        <div className="w-4 h-4 flex items-center justify-center">
                            {isHovered ? (isThinkingExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />) : <Brain size={14} className="text-primary/60 animate-pulse" />}
                        </div>
                        <span>{thought.isClosed ? "深度思考" : "深度思考中..."}</span>
                    </button>
                    {isThinkingExpanded && (
                        <div className="px-4 pb-3 text-xs leading-relaxed text-muted-foreground/60 italic font-medium border-t border-border/20 pt-2 break-all">
                            <ReactMarkdown remarkPlugins={[remarkGfm]} components={MarkdownComponents}>
                                {thought.content || "正在审视上下文..."}
                            </ReactMarkdown>
                        </div>
                    )}
                </div>
            )}

            {plan && <PlanTodoView content={plan.content} />}

            {mainContent && (
                <div className="text-sm leading-relaxed text-foreground/90 font-medium relative [&_p]:mb-6 last:[&_p]:mb-0 break-all w-full min-w-0">
                    <ReactMarkdown remarkPlugins={[remarkGfm]} components={MarkdownComponents}>{mainContent}</ReactMarkdown>
                    {isStreaming && !mainContent.endsWith(".") && <span className="inline-flex gap-1 ml-1 animate-pulse text-primary font-black">_</span>}
                </div>
            )}

            {isLatest && isLoading && msg.status && (
                <div className="flex items-center gap-2 px-2 py-1.5 bg-primary/5 border border-primary/10 rounded-lg w-fit animate-in fade-in zoom-in-95 mt-2">
                    <Zap size={10} className="text-primary animate-pulse" />
                    <span className="text-[10px] font-bold text-primary/70 uppercase tracking-wider">{msg.status}</span>
                </div>
            )}
        </div>
    );
};

interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    agent_id?: string;
    agent_name?: string;
    agent_avatar?: string;
    steps?: number;
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

interface Report {
    title: string;
    product: string;
    status: string;
    timestamp: string;
    details: string;
}

export default function ExecutionConsole() {
    const [agents, setAgents] = useState<Agent[]>([]);
    const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
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
    const [flowWidth, setFlowWidth] = useState(380);
    const [isResizing, setIsResizing] = useState(false);
    const [isHovering, setIsHovering] = useState(false);
    const [isAtBottom, setIsAtBottom] = useState(true);
    const [showScrollButton, setShowScrollButton] = useState(false);
    const [hasNewMessages, setHasNewMessages] = useState(false);
    
    const scrollRef = useRef<HTMLDivElement>(null);
    const viewportRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const isProgrammaticScroll = useRef(false);
    const agentsRef = useRef<Agent[]>([]);

    const scrollToBottom = (behavior: ScrollBehavior = "smooth") => {
        if (viewportRef.current) {
            isProgrammaticScroll.current = true;
            setShowScrollButton(false);
            viewportRef.current.scrollTo({ top: viewportRef.current.scrollHeight, behavior });
            setTimeout(() => {
                isProgrammaticScroll.current = false;
                setIsAtBottom(true);
                setHasNewMessages(false);
            }, 500);
        }
    };

    const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
        if (isProgrammaticScroll.current) return;
        const target = e.currentTarget;
        const distanceToBottom = target.scrollHeight - target.scrollTop - target.clientHeight;
        const atBottom = distanceToBottom < 20;
        setIsAtBottom(atBottom);
        setShowScrollButton(distanceToBottom > 100);
        if (atBottom) setHasNewMessages(false);
    };

    useEffect(() => {
        if (!messages.length) return;
        if (!isHovering && isAtBottom) scrollToBottom("auto");
        else if (!isAtBottom) setHasNewMessages(true);
    }, [messages, isLoading]);

    const handleMouseDown = (e: React.MouseEvent) => {
        setIsResizing(true);
        const startX = e.clientX;
        const startWidth = flowWidth;
        document.body.style.userSelect = "none";
        const handleMouseMove = (e: MouseEvent) => {
            const newWidth = startWidth + (e.clientX - startX);
            if (newWidth > 320 && newWidth < 800) setFlowWidth(newWidth);
        };
        const handleMouseUp = () => {
            setIsResizing(false);
            document.removeEventListener("mousemove", handleMouseMove);
            document.removeEventListener("mouseup", handleMouseUp);
            document.body.style.cursor = "default";
            document.body.style.userSelect = "auto";
        };
        document.addEventListener("mousemove", handleMouseMove);
        document.addEventListener("mouseup", handleMouseUp);
        document.body.style.cursor = "col-resize";
    };

    useEffect(() => {
        const fetchAgents = async () => {
            try {
                const response = await fetch("http://localhost:8000/api/agents");
                if (!response.ok) throw new Error("无法获取智能体列表");
                const data = await response.json();
                if (data) {
                    setAgents(data);
                    agentsRef.current = data;
                    setTimeout(() => textareaRef.current?.focus(), 100);
                }
            } catch (err) { console.error("Fetch agents error:", err); }
        };
        fetchAgents();
    }, []);

    const handleSend = async () => {
        if (!inputValue.trim() || isLoading) return;
        let sessionId = currentSessionId;
        if (!sessionId) {
            const { data } = await supabase.from("chat_sessions").insert([{ title: "新会话" }]).select().single();
            if (data) { sessionId = data.id; setCurrentSessionId(sessionId); }
        }
        const mentionedAgent = agents.find((a) => inputValue.includes(`@${a.name}`));
        const targetAgent = mentionedAgent || agents.find((a) => a.identifier === "primary_agent");
        if (!targetAgent) return;

        const userMsg: Message = { id: Date.now().toString(), role: "user", content: inputValue, timestamp: Date.now() };
        const isFirstMessage = messages.length === 0;
        setMessages((prev) => [...prev, userMsg]);
        setInputValue("");
        setIsLoading(true);
        setShowAgentMenu(false);

        const assistantId = (Date.now() + 1).toString();
        try {
            if (isFirstMessage) {
                fetch("http://localhost:8000/api/chat/summarize", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ content: userMsg.content }) })
                    .then(res => res.json()).then(async data => { if (data.title && sessionId) { setSessionTitle(data.title); await supabase.from("chat_sessions").update({ title: data.title }).eq("id", sessionId); } });
            }

            const assistantMsg: Message = { id: assistantId, role: "assistant", content: "", agent_name: targetAgent.name, agent_avatar: targetAgent.avatar, timestamp: Date.now() };
            setMessages((prev) => [...prev, assistantMsg]);

            const response = await fetch("http://localhost:8000/api/chat/stream", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ agent_id: targetAgent.identifier, content: userMsg.content }) });
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
                            if (event.agent_id && event.agent_id !== lastAgentId) {
                                lastAgentId = event.agent_id;
                                currentAssistantId = (Date.now() + Math.random()).toString();
                                const newAgent = agentsRef.current.find(a => a.identifier === event.agent_id);
                                setMessages(prev => [...prev, { id: currentAssistantId, role: "assistant", content: event.content, agent_id: event.agent_id, agent_name: newAgent?.name || event.agent_id, agent_avatar: newAgent?.avatar || "", timestamp: Date.now() }]);
                            } else {
                                setMessages(prev => prev.map(msg => msg.id === currentAssistantId ? { ...msg, content: (msg.content || "") + event.content } : msg));
                            }
                        } else if (event.type === "status") {
                            setMessages(prev => prev.map(msg => msg.id === currentAssistantId ? { ...msg, status: event.content } : msg));
                        } else if (event.type === "error") {
                            setMessages(prev => [...prev, { id: Date.now().toString(), role: "assistant", content: `\n\n[ERROR]: ${event.content}\n`, agent_name: "System", timestamp: Date.now() }]);
                        }
                    } catch (e) {}
                }
            }
            setActiveReport({ title: "全域策略执行报告", product: "智能决策输出", status: "Completed", timestamp: new Date().toLocaleTimeString(), details: "分析已完成。" });
        } catch (error) {
            setMessages(prev => prev.map(msg => msg.id === assistantId ? { ...msg, content: "系统异常，请稍后再试。" } : msg));
        } finally {
            setIsLoading(false);
            setTimeout(() => textareaRef.current?.focus(), 0);
        }
    };

    return (
        <div className="flex h-screen bg-background text-foreground overflow-hidden font-sans relative">
            <aside className={`flex flex-col z-50 shrink-0 transition-all duration-300 ease-in-out bg-sidebar relative ${isSidebarOpen ? "w-[240px] border-r border-sidebar-border/40" : "w-0 border-none"}`}>
                <div className="w-[240px] flex flex-col h-full">
                    <header className="h-12 flex items-center justify-between px-4 shrink-0">
                        <div className="flex items-center gap-2"><div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-primary-foreground font-black text-xl">A</div><span className="font-black text-sm uppercase">Autonomy</span></div>
                        <Button variant="ghost" size="icon" onClick={() => setIsSidebarOpen(false)} className="h-8 w-8"><PanelLeft size={16} /></Button>
                    </header>
                    <div className="p-4 flex-1 flex flex-col overflow-hidden">
                        <Button onClick={() => { setMessages([]); setCurrentSessionId(null); setSessionTitle("新会话"); }} className="w-full justify-start gap-3 bg-primary/10 text-primary rounded-xl h-11 text-xs font-bold transition-all"><Plus size={18} />开启新会话</Button>
                        <ScrollArea className="flex-1 mt-4"><div className="space-y-1.5"><div className="px-4 py-2 text-[10px] font-black opacity-30 uppercase tracking-widest">最近会话</div><button className="w-full text-left p-3.5 rounded-xl bg-primary/10 text-primary flex items-center gap-3"><MessageSquare size={14} /><div className="truncate flex-1 text-xs font-semibold">{sessionTitle}</div></button></div></ScrollArea>
                    </div>
                </div>
            </aside>

            <section style={{ width: isFlowOpen ? `${flowWidth}px` : "0px" }} className={`flex flex-col z-40 shrink-0 bg-background relative h-full overflow-hidden ${isFlowOpen ? "border-r border-border/40" : ""}`}>
                {isFlowOpen && <div className="absolute -right-1 top-0 w-2 h-full cursor-col-resize z-50 hover:bg-primary/30" onMouseDown={handleMouseDown} />}
                <header className="h-12 border-b border-border/40 flex items-center justify-between px-4 shrink-0 bg-background/50 backdrop-blur-md">
                    <div className="flex items-center gap-2">{!isSidebarOpen && <Button variant="ghost" size="icon" onClick={() => setIsSidebarOpen(true)} className="h-8 w-8"><PanelLeft size={16} className="rotate-180" /></Button>}<input value={sessionTitle} onChange={(e) => setSessionTitle(e.target.value)} className="bg-transparent border-none text-[13px] font-bold outline-none flex-1" placeholder="输入标题..." /></div>
                    <Button variant="ghost" size="icon" onClick={() => setIsFlowOpen(false)} className="h-8 w-8"><PanelLeft size={16} /></Button>
                </header>

                <div className="flex-1 min-h-0 relative flex flex-col bg-muted/5" onMouseEnter={() => setIsHovering(true)} onMouseLeave={() => setIsHovering(false)}>
                    <ScrollArea className="flex-1 h-0" viewportRef={viewportRef} onScroll={handleScroll}>
                        <div className="p-6 space-y-8 pb-12">
                            {messages.length === 0 && <div className="space-y-4"><div className="flex items-center gap-3 text-primary"><Sparkles size={20} /><h3 className="text-sm font-bold uppercase">就绪</h3></div><p className="text-xs font-medium text-muted-foreground">请输入指令启动策略分析。</p></div>}
                            {messages.map((msg, index) => (
                                <div key={msg.id}>{msg.role === "assistant" ? <AssistantMessageItem msg={msg} isLatest={index === messages.length - 1} isLoading={isLoading} /> : <div className="flex flex-col items-end space-y-1.5"><span className="text-[10px] font-black text-primary/40 uppercase">You</span><div className="bg-primary/5 border border-primary/20 p-4 rounded-2xl rounded-tr-none text-sm font-semibold max-w-[90%] text-primary">{msg.content}</div></div>}</div>
                            ))}
                        </div>
                    </ScrollArea>
                    {showScrollButton && (
                        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-50">
                            <Button size="sm" onClick={() => scrollToBottom("smooth")} className="rounded-full shadow-lg bg-primary text-primary-foreground text-[10px] font-bold gap-2 h-9 px-4">
                                {hasNewMessages ? <Sparkles size={14} className="fill-current" /> : <ChevronDown size={14} />}
                                <span>{hasNewMessages ? "查看新消息" : "回到最底部"}</span>
                            </Button>
                        </div>
                    )}
                </div>

                <div className="p-6 bg-background relative">
                    {showAgentMenu && (
                        <Card className="absolute bottom-full left-6 w-56 bg-popover border shadow-2xl p-1 z-50 rounded-xl mb-2">
                            {agents.filter(a => a.name.toLowerCase().includes(mentionQuery.toLowerCase())).map((agent, index) => (
                                <button key={agent.id} onClick={() => { setInputValue(inputValue.substring(0, inputValue.lastIndexOf("@")) + "@" + agent.name + " "); setShowAgentMenu(false); }} className={`w-full flex items-center gap-2.5 p-1.5 rounded-lg text-left ${index === selectedIndex ? "bg-primary/20" : "hover:bg-primary/10"}`}>
                                    <div className="w-6 h-6 rounded-md overflow-hidden bg-muted"><img src={agent.avatar} className="w-full h-full object-cover" /></div>
                                    <div className="flex flex-col min-w-0"><span className="text-[11px] font-bold truncate">{agent.name}</span><span className="text-[9px] text-muted-foreground truncate">{agent.role}</span></div>
                                </button>
                            ))}
                        </Card>
                    )}
                    <Card className="bg-background/50 border-border/40 p-1.5 flex flex-col gap-1 rounded-xl">
                        <textarea ref={textareaRef} value={inputValue} onChange={(e) => { setInputValue(e.target.value); const lastAt = e.target.value.lastIndexOf("@"); if (lastAt !== -1 && (lastAt === 0 || e.target.value[lastAt-1] === " ")) { setShowAgentMenu(true); setMentionQuery(e.target.value.substring(lastAt+1)); } else { setShowAgentMenu(false); } }} onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }} placeholder="输入指令或使用 @ 呼叫智能体..." className="w-full bg-transparent border-none p-3 text-sm font-medium resize-none min-h-[90px] outline-none" />
                        <div className="flex items-center justify-between px-2 pb-1.5"><div className="flex items-center gap-1"><Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground"><Paperclip size={16} /></Button><Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground" onClick={() => setShowAgentMenu(!showAgentMenu)}><AtSign size={16} /></Button></div><Button size="icon" disabled={!inputValue.trim() || isLoading} onClick={handleSend} className="h-9 w-9 rounded-full bg-primary text-primary-foreground">{isLoading ? <StopCircle size={16} className="animate-spin" /> : <Send size={16} />}</Button></div>
                    </Card>
                </div>
            </section>

            <div className="flex-1 flex flex-col min-w-0 bg-background relative h-full">
                <header className="h-12 border-b border-border/40 flex items-center justify-between px-6 shrink-0 sticky top-0 z-20 bg-background">
                    <div className="flex items-center gap-4">{!isFlowOpen && <Button variant="ghost" size="icon" onClick={() => setIsFlowOpen(true)} className="h-8 w-8"><PanelLeft size={16} className="rotate-180" /></Button>}<div className="text-[11px] font-bold uppercase opacity-50">控制台 / 执行面板</div></div>
                    <div className="flex -space-x-2"><TooltipProvider>{agents.map(a => <Tooltip key={a.id}><TooltipTrigger asChild><Avatar className="w-7 h-7 border-2 border-background ring-1 ring-border/50"><AvatarImage src={a.avatar} /><AvatarFallback className="text-[10px]">{a.name.charAt(0)}</AvatarFallback></Avatar></TooltipTrigger><TooltipContent side="bottom" className="text-xs font-bold p-2">{a.name} - {a.role}</TooltipContent></Tooltip>)}</TooltipProvider></div>
                </header>
                <main className="flex-1 p-6 relative overflow-hidden">
                    <div className="h-full bg-card rounded-2xl border border-border/40 relative overflow-hidden flex flex-col">
                        {activeReport ? (
                            <ScrollArea className="flex-1 p-8"><div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
                                <div className="border-b pb-6"><Badge className="bg-primary/10 text-primary mb-4">{activeReport.status}</Badge><h2 className="text-4xl font-black italic tracking-tighter">{activeReport.title}</h2></div>
                                <Card className="p-8 space-y-6"><div className="flex items-center gap-3"><div className="w-2 h-5 bg-primary rounded-full" /><h4 className="text-xs font-black uppercase tracking-widest">策略分析摘要</h4></div><p className="text-sm leading-relaxed text-muted-foreground font-medium bg-muted/10 p-6 rounded-xl border-dashed border">{activeReport.details} 本次分析已同步检索实时波动数据。</p></Card>
                            </div></ScrollArea>
                        ) : (
                            <div className="flex-1 flex flex-col items-center justify-center opacity-20 grayscale"><Zap size={64} className="animate-pulse" /><h3 className="text-2xl font-black uppercase tracking-widest mt-4">准备就绪</h3></div>
                        )}
                    </div>
                </main>
            </div>
        </div>
    );
}