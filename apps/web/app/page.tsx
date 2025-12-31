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
                    jsonStr.includes('"chartType"') &&
                    jsonStr.includes('"data"')
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
                    // Calculate indentation depth
                    const indentMatch = line.match(/^(\s*)/);
                    const indentLevel = indentMatch ? Math.floor(indentMatch[0].length / 2) : 0;
                    
                    const trimmedLine = line.trim();
                    
                    // Regex to check for explicit todo markers: [ ] or [x]
                    const isTodoTask = /^[-*+]\s*\[[\sxX]\]/.test(trimmedLine);
                    const isDone = /^[-*+]\s*\[[xX]\]/.test(trimmedLine);
                    
                    // Clean content: remove bullet points, checkboxes and UNWRAP <call> tags
                    const cleanContent = trimmedLine
                        .replace(/^[-*+]\s*(\[[\sxX]\])?\s*/, "")
                        .replace(/^\d+\.\s*/, "")
                        // Unwrap <call> tags but keep content, making the mention bold
                        .replace(/<call>\s*(@\w+)\s*(.*?)\s*<\/call>/gs, "**$1** $2")
                        .replace(/<call>\s*(@\w+)?\s*(.*?)$/gs, "**$1** $2"); // Handle streaming

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
                                    ) : (
                                        <div className="w-3.5 h-3.5 rounded-full border-2 border-primary/30 group-hover:border-primary/50 transition-colors" />
                                    )}
                                </div>
                            ) : (
                                // Render a simple bullet for non-task list items, or nothing for plain text
                                <div className="mt-2 shrink-0 flex justify-center w-3.5">
                                    <div className="w-1 h-1 rounded-full bg-muted-foreground/30" />
                                </div>
                            )}
                            <div
                                className={`text-[13px] font-medium leading-relaxed max-w-none flex-1 ${
                                    isDone
                                        ? "text-muted-foreground/50 line-through decoration-primary/20"
                                        : "text-foreground/80"
                                }`}
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

// --- Skill Action Renderer ---
const SkillActionView = ({ content, isClosed }: { content: string, isClosed: boolean }) => {
    let skillId = "未知技能";
    let params = {};
    
    try {
        const data = JSON.parse(content);
        skillId = data.skill_id || skillId;
        params = data.params || {};
    } catch (e) {
        // 流式传输中 JSON 可能不完整
        const idMatch = content.match(/"skill_id"\s*:\s*"([^"]*)"/);
        if (idMatch) skillId = idMatch[1];
    }

    return (
        <div className="my-4 bg-muted/30 border border-border/40 rounded-xl overflow-hidden shadow-sm animate-in fade-in slide-in-from-bottom-2">
            <div className="bg-muted/50 px-3 py-2 border-b border-border/40 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${isClosed ? 'bg-green-500' : 'bg-amber-500 animate-pulse'}`} />
                    <span className="text-[10px] font-black uppercase tracking-widest text-foreground/70">
                        技能执行: {skillId}
                    </span>
                </div>
                {!isClosed && (
                    <span className="text-[9px] font-mono text-muted-foreground animate-pulse">
                        EXECUTING...
                    </span>
                )}
            </div>
            <div className="p-3 font-mono text-[11px] text-muted-foreground/80 bg-black/5 dark:bg-white/5">
                <div className="flex gap-2">
                    <span className="text-primary/60">Input:</span>
                    <span className="break-all">{JSON.stringify(params)}</span>
                </div>
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

    // Loading State: Show animation if content is empty during loading
    if (isLatest && isLoading && !content) {
        return (
            <div className="space-y-3 w-full min-w-0 animate-in fade-in duration-500">
                <div className="flex items-center gap-2.5">
                    <div className="w-6 h-6 rounded-md bg-primary/10 overflow-hidden ring-1 ring-primary/20 flex items-center justify-center">
                        {msg.agent_avatar ? (
                            <img
                                src={msg.agent_avatar}
                                alt={msg.agent_name}
                                className="w-full h-full object-cover"
                            />
                        ) : (
                            <span className="text-[10px] font-bold">
                                {msg.agent_name?.charAt(0)}
                            </span>
                        )}
                    </div>
                    <span className="text-[11px] font-bold text-foreground/80 tracking-widest">
                        {msg.agent_name}
                    </span>
                </div>
                <div className="flex items-center gap-2 bg-muted/20 p-4 rounded-2xl w-fit border border-border/40">
                    <span className="flex gap-1.5 items-center">
                        <span className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce [animation-duration:0.8s] [animation-delay:-0.3s]"></span>
                        <span className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce [animation-duration:0.8s] [animation-delay:-0.15s]"></span>
                        <span className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce [animation-duration:0.8s]"></span>
                    </span>
                    <span className="text-[10px] font-bold text-muted-foreground/60 uppercase tracking-widest ml-2">
                        思考中...
                    </span>
                </div>
            </div>
        );
    }

    // Tags Parsing Logic - Support multiple blocks
    const parseAllTags = (startTag: string, endTag: string) => {
        const results = [];
        let cursor = 0;

        while (true) {
            const startIdx = content.indexOf(startTag, cursor);
            if (startIdx === -1) break;

            const endIdx = content.indexOf(endTag, startIdx + startTag.length);
            results.push({
                content:
                    endIdx !== -1
                        ? content.substring(startIdx + startTag.length, endIdx)
                        : content.substring(startIdx + startTag.length),
                isClosed: endIdx !== -1,
                startIdx,
                endIdx,
            });

            if (endIdx === -1) break;
            cursor = endIdx + endTag.length;
        }
        return results;
    };

    const allThoughts = parseAllTags("<thought>", "</thought>");
    const allPlans = parseAllTags("<plan>", "</plan>");
    const allActions = parseAllTags("<action>", "</action>");

    // For UI display, we focus on the LATEST block during streaming,
    // but can show historical ones if needed.
    const thought = allThoughts[allThoughts.length - 1] || null;
    const plan = allPlans[allPlans.length - 1] || null;
    const action = allActions[allActions.length - 1] || null;

    const isStreaming = isLatest && isLoading;

    let mainContent = content;

    // Strip blocks that have dedicated UI renderers
    const blocksToHide = [
        { start: "<thought>", end: "</thought>" },
        { start: "<plan>", end: "</plan>" },
        { start: "<thinking>", end: "</thinking>" },
        { start: "<action>", end: "</action>" },
    ];

    blocksToHide.forEach((block) => {
        while (true) {
            const s = mainContent.indexOf(block.start);
            if (s === -1) break;
            const e = mainContent.indexOf(block.end, s);
            if (e !== -1) {
                mainContent =
                    mainContent.substring(0, s) +
                    mainContent.substring(e + block.end.length);
            } else {
                mainContent = mainContent.substring(0, s);
                break;
            }
        }
    });

    // Special treatment for <call> - convert to highlighted markdown instead of stripping
    mainContent = mainContent.replace(/<call>\s*(@\w+)\s*(.*?)\s*<\/call>/gs, (match, agent, task) => {
        return `\n\n> **${agent}** ${task}\n\n`;
    });

    // Also handle unclosed <call> during streaming
    const unclosedCall = mainContent.match(/<call>\s*(@\w+)?\s*([^<]*)$/s);
    if (isStreaming && unclosedCall) {
        const agent = unclosedCall[1] || "";
        const task = unclosedCall[2] || "";
        mainContent = mainContent.substring(0, unclosedCall.index) + `\n\n> **${agent}** ${task}`;
    }

    // --- 预防流式闪烁：隐藏末尾的潜在标签前缀 ---
    // 如果正文以 '<', '</', '<p', '<t' 等开头或结尾，可能是标签正在到达
    const partialTagMatch = mainContent.match(/<[\/a-zA-Z0-9]*$/);
    if (isStreaming && partialTagMatch) {
        mainContent = mainContent.substring(0, partialTagMatch.index);
    }

    mainContent = mainContent.trim();

    return (
        <div className="space-y-3 w-full min-w-0 overflow-hidden">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                    <div className="w-6 h-6 rounded-md bg-primary/10 overflow-hidden ring-1 ring-primary/20 flex items-center justify-center">
                        {msg.agent_avatar ? (
                            <img
                                src={msg.agent_avatar}
                                alt={msg.agent_name}
                                className="w-full h-full object-cover"
                            />
                        ) : (
                            <span className="text-[10px] font-bold">
                                {msg.agent_name?.charAt(0)}
                            </span>
                        )}
                    </div>
                    <span className="text-[11px] font-bold text-foreground/80 tracking-widest">
                        {msg.agent_name}
                    </span>
                </div>
                <span className="text-[9px] font-medium text-muted-foreground/50 tabular-nums">
                    {new Date(msg.timestamp).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                    })}
                </span>
            </div>

            {/* --- Thinking Block --- */}
            {thought && (
                <div
                    className={`rounded-xl overflow-hidden transition-all w-full min-w-0 ${
                        isThinkingExpanded
                            ? "bg-muted/30 border border-border/40"
                            : "bg-transparent border-transparent"
                    }`}
                >
                    <button
                        onClick={() =>
                            setIsThinkingExpanded(!isThinkingExpanded)
                        }
                        onMouseEnter={() => setIsHovered(true)}
                        onMouseLeave={() => setIsHovered(false)}
                        className="flex items-center gap-2 px-1.5 py-1.5 hover:text-foreground/80 transition-colors text-[10px] font-bold text-muted-foreground/70 uppercase tracking-tight"
                    >
                        <div className="w-4 h-4 flex items-center justify-center">
                            {isHovered ? (
                                isThinkingExpanded ? (
                                    <ChevronDown size={14} />
                                ) : (
                                    <ChevronRight size={14} />
                                )
                            ) : (
                                <Brain size={14} className="text-primary/60 animate-pulse" />
                            )}
                        </div>
                        <span className="flex-1 text-left flex items-center">
                            {thought.isClosed ? "深度思考" : (
                                <>
                                    深度思考中
                                    <span className="inline-flex ml-0.5">
                                        <span className="animate-[pulse_1.5s_infinite] [animation-delay:0s]">.</span>
                                        <span className="animate-[pulse_1.5s_infinite] [animation-delay:0.3s]">.</span>
                                        <span className="animate-[pulse_1.5s_infinite] [animation-delay:0.6s]">.</span>
                                    </span>
                                </>
                            )}
                        </span>
                    </button>
                    {isThinkingExpanded && (
                        <div className="px-4 pb-3 text-xs leading-relaxed text-muted-foreground/60 italic font-medium border-t border-border/20 pt-2 break-all">
                            <ReactMarkdown
                                remarkPlugins={[remarkGfm]}
                                components={MarkdownComponents}
                            >
                                {thought.content || "正在审视上下文..."}
                            </ReactMarkdown>
                        </div>
                    )}
                </div>
            )}

            {/* --- Action Plan Block --- */}
            {plan && <PlanTodoView content={plan.content} />}

            {/* --- Skill Action Block (Nexus V4) --- */}
            {action && <SkillActionView content={action.content} isClosed={action.isClosed} />}

            {/* --- Main Response --- */}
            {mainContent && (
                <div className="text-sm leading-relaxed text-foreground/90 font-medium relative [&_p]:mb-6 last:[&_p]:mb-0 break-all w-full min-w-0">
                    <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={MarkdownComponents}
                    >
                        {mainContent}
                    </ReactMarkdown>
                    {isStreaming && (thought?.isClosed || !thought) && (plan?.isClosed || !plan) && (
                        <span className="inline-flex gap-1 ml-1 items-center align-middle">
                            <span className="w-1 h-1 rounded-full bg-primary animate-bounce [animation-duration:0.8s] [animation-delay:-0.3s]"></span>
                            <span className="w-1 h-1 rounded-full bg-primary animate-bounce [animation-duration:0.8s] [animation-delay:-0.15s]"></span>
                            <span className="w-1 h-1 rounded-full bg-primary animate-bounce [animation-duration:0.8s]"></span>
                        </span>
                    )}
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
    const [currentSessionId, setCurrentSessionId] = useState<string | null>(
        null
    );
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
    const scrollRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const handleMouseDown = (e: React.MouseEvent) => {
        setIsResizing(true);
        const startX = e.clientX;
        const startWidth = flowWidth;
        document.body.style.userSelect = "none";

        const handleMouseMove = (e: MouseEvent) => {
            const newWidth = startWidth + (e.clientX - startX);
            if (newWidth > 320 && newWidth < 800) {
                setFlowWidth(newWidth);
            }
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

    const agentsRef = useRef<Agent[]>([]);

    useEffect(() => {
        const fetchAgents = async () => {
            const { data } = await supabase
                .from("agents")
                .select("*")
                .order("identifier");
            if (data) {
                setAgents(data);
                agentsRef.current = data;
            }
        };
        fetchAgents();
    }, []);

    useEffect(() => {
        let ws: WebSocket | null = null;
        let reconnectTimeout: NodeJS.Timeout;

        const connect = () => {
            ws = new WebSocket("ws://localhost:8000/ws/ops");

            ws.onmessage = (event) => {
                try {
                    const payload = JSON.parse(event.data);
                    if (payload.type === "agent_message") {
                        const msgData = payload.data;
                        const { sender, subject, content } = msgData;

                        if (subject === "task_stream_chunk") {
                            const agent = agentsRef.current.find(
                                (a) => a.identifier === sender
                            );
                            const messageId = `stream_${sender}`;

                            setMessages((prev) => {
                                const existing = prev.find(
                                    (m) => m.id === messageId
                                );
                                if (existing) {
                                    return prev.map((m) =>
                                        m.id === messageId
                                            ? {
                                                  ...m,
                                                  content:
                                                      content.full_content_so_far,
                                              }
                                            : m
                                    );
                                } else {
                                    return [
                                        ...prev,
                                        {
                                            id: messageId,
                                            role: "assistant",
                                            content: content.chunk,
                                            agent_id: sender,
                                            agent_name: agent?.name || sender,
                                            agent_avatar: agent?.avatar || "",
                                            timestamp: Date.now(),
                                        },
                                    ];
                                }
                            });
                        }

                        if (subject === "task_result") {
                            const messageId = `stream_${sender}`;
                            setMessages((prev) =>
                                prev.map((m) =>
                                    m.id === messageId
                                        ? { ...m, content: content.result }
                                        : m
                                )
                            );
                        }
                    }
                } catch (e) {
                    console.error("WS error:", e);
                }
            };

            ws.onclose = () => {
                console.log("WS closed, reconnecting...");
                reconnectTimeout = setTimeout(connect, 3000);
            };
        };

        connect();

        return () => {
            if (ws) ws.close();
            clearTimeout(reconnectTimeout);
        };
    }, []);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, isLoading]);

    const handleSend = async () => {
        if (!inputValue.trim() || isLoading) return;

        let sessionId = currentSessionId;

        // 如果是新会话的第一条消息，先创建会话
        if (!sessionId) {
            const { data, error } = await supabase
                .from("chat_sessions")
                .insert([{ title: "新会话" }])
                .select()
                .single();

            if (data) {
                sessionId = data.id;
                setCurrentSessionId(sessionId);
            }
        }

        const mentionedAgent = agents.find((a) =>
            inputValue.includes(`@${a.name}`)
        );

        // 严格模式：仅使用已加载的真实 Agent 数据
        // 如果找不到提及的 Agent，则回退到 CEO Agent
        const defaultAgent = agents.find((a) => a.identifier === "ceo_agent");
        const targetAgent = mentionedAgent || defaultAgent;
        
        // 如果连默认 CEO 都没有（说明数据未加载或配置错误），则禁止发送
        if (!targetAgent) {
            console.error("错误: 无法定位目标智能体，且未找到默认 CEO 智能体。");
            return;
        }

        const targetName = targetAgent.name;
        const targetId = targetAgent.identifier;
        const targetAvatar = targetAgent.avatar;

        const userMsg: Message = {
            id: Date.now().toString(),
            role: "user",
            content: inputValue,
            timestamp: Date.now(),
        };

        const isFirstMessage = messages.length === 0;
        setMessages((prev) => [...prev, userMsg]);
        const currentInput = inputValue; // 保存当前输入用于总结
        setInputValue("");
        setIsLoading(true);
        setShowAgentMenu(false);

        const assistantId = (Date.now() + 1).toString();

        try {
            // 并行发起总结请求 (仅针对第一条消息)
            if (isFirstMessage) {
                fetch("http://localhost:8000/api/chat/summarize", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ content: currentInput }),
                })
                    .then((res) => res.json())
                    .then(async (data) => {
                        if (data.title) {
                            setSessionTitle(data.title);
                            // 更新数据库中的标题
                            if (sessionId) {
                                await supabase
                                    .from("chat_sessions")
                                    .update({ title: data.title })
                                    .eq("id", sessionId);
                            }
                        }
                    })
                    .catch((err) => console.error("Summarize error:", err));
            }

            const assistantMsg: Message = {
                id: assistantId,
                role: "assistant",
                content: "",
                agent_name: targetName,
                agent_avatar: targetAvatar,
                steps: 0,
                timestamp: Date.now(),
            };

            setMessages((prev) => [...prev, assistantMsg]);

            const response = await fetch(
                "http://localhost:8000/api/chat/stream",
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        agent_id: targetId,
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
            let lastAgentId = targetId;

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                
                // 处理 JSONL (每行一个 JSON)
                const lines = buffer.split("\n");
                buffer = lines.pop() || ""; // 最后一行可能不完整，留到下一轮

                for (const line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const event = JSON.parse(line);
                        
                        if (event.type === "stream") {
                            const newAgentId = event.agent_id;
                            const chunk = event.content;

                            // 如果 Agent 切换了，创建一个新的消息条目
                            if (newAgentId && newAgentId !== lastAgentId) {
                                lastAgentId = newAgentId;
                                currentAssistantId = (Date.now() + Math.random()).toString();
                                
                                const newAgent = agentsRef.current.find(a => a.identifier === newAgentId);
                                
                                const newMsg: Message = {
                                    id: currentAssistantId,
                                    role: "assistant",
                                    content: chunk,
                                    agent_id: newAgentId,
                                    agent_name: newAgent?.name || newAgentId,
                                    agent_avatar: newAgent?.avatar || "",
                                    timestamp: Date.now(),
                                };
                                
                                setMessages(prev => [...prev, newMsg]);
                            } else {
                                // 否则，更新当前消息
                                setMessages((prev) =>
                                    prev.map((msg) =>
                                        msg.id === currentAssistantId
                                            ? { ...msg, content: (msg.content || "") + chunk }
                                            : msg
                                    )
                                );
                            }
                        } else if (event.type === "error") {
                            setMessages((prev) => [
                                ...prev,
                                {
                                    id: Date.now().toString(),
                                    role: "assistant",
                                    content: `\n\n[ERROR]: ${event.content}\n`,
                                    agent_name: "System",
                                    timestamp: Date.now()
                                }
                            ]);
                        }
                    } catch (e) {
                        console.error("解析 JSON 流失败:", e, line);
                    }
                }
            }

            setActiveReport({
                title: "全域策略执行报告",
                product: "智能决策输出",
                status: "Completed",
                timestamp: new Date().toLocaleTimeString(),
                details: "基于智能体矩阵的实时分析已完成。",
            });
        } catch (error) {
            console.error("Streaming error:", error);
            setMessages((prev) =>
                prev.map((msg) =>
                    msg.id === assistantId
                        ? {
                              ...msg,
                              content:
                                  "抱歉，系统出现异常，我暂时无法完成此项任务，请稍后再试。",
                          }
                        : msg
                )
            );
        } finally {
            setIsLoading(false);
        }
    };

    const startNewSession = () => {
        setMessages([]);
        setActiveReport(null);
        setSessionTitle("新会话");
        setCurrentSessionId(null);
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

                    <div className="p-4 pt-6 flex-1 flex flex-col overflow-hidden">
                        <div className="mb-4">
                            <Button
                                onClick={startNewSession}
                                className="w-full justify-start gap-3 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 shadow-none rounded-xl h-11 text-xs font-bold transition-all px-4"
                            >
                                <Plus size={18} />
                                开启新会话
                            </Button>
                        </div>

                        <ScrollArea className="flex-1 w-full">
                            <div className="space-y-1.5 w-full">
                                <div className="px-4 py-2 text-[10px] font-black text-sidebar-foreground/30 uppercase tracking-[0.2em] mb-1">
                                    最近会话
                                </div>
                                <button className="w-full max-w-full overflow-hidden text-left p-3.5 px-4 rounded-xl bg-primary/10 border border-primary/20 text-xs font-semibold text-primary flex items-center gap-3 group transition-all ring-1 ring-primary/5">
                                    <MessageSquare
                                        size={14}
                                        className="text-primary/70 shrink-0"
                                    />
                                    <div className="truncate flex-1 max-w-full w-0">
                                        {sessionTitle}
                                    </div>
                                    <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse shrink-0" />
                                </button>
                                <button className="w-full max-w-full overflow-hidden text-left p-3.5 px-4 rounded-xl hover:bg-sidebar-accent hover:text-foreground text-xs font-semibold text-sidebar-foreground/50 flex items-center gap-3 group transition-all border border-transparent">
                                    <Clock
                                        size={14}
                                        className="text-sidebar-foreground/30 shrink-0"
                                    />
                                    <div className="truncate flex-1 max-w-full w-0">
                                        历史分析报告 12/28
                                    </div>
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
                style={{ width: isFlowOpen ? `${flowWidth}px` : "0px" }}
                className={`flex flex-col z-40 shrink-0 bg-background relative h-full overflow-hidden ${
                    isFlowOpen ? "border-r border-border/40" : "border-none"
                } ${
                    !isResizing
                        ? "transition-[width,border] duration-300 ease-in-out"
                        : ""
                }`}
            >
                {isFlowOpen && (
                    <div
                        className="absolute -right-1 top-0 w-2 h-full cursor-col-resize z-50 hover:bg-primary/30 transition-colors"
                        onMouseDown={handleMouseDown}
                    />
                )}
                <div
                    className={`flex flex-col flex-1 min-h-0 ${
                        !isResizing ? "overflow-hidden" : ""
                    }`}
                >
                    <header className="h-12 border-b border-border/40 flex items-center justify-between px-4 shrink-0 bg-background/50 backdrop-blur-md">
                        <div className="flex items-center gap-2">
                            {!isSidebarOpen && (
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    onClick={() => setIsSidebarOpen(true)}
                                    className="h-8 w-8 text-muted-foreground hover:text-background"
                                >
                                    <PanelLeft
                                        size={16}
                                        className="rotate-180"
                                    />
                                </Button>
                            )}
                            <input
                                value={sessionTitle}
                                onChange={(e) =>
                                    setSessionTitle(e.target.value)
                                }
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

                    <ScrollArea className="flex-1 h-0 bg-muted/5">
                        <div className="p-6 space-y-8 pb-12 max-w-full">
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

                            {messages.map((msg, index) => (
                                <div
                                    key={msg.id}
                                    className="space-y-4 animate-in fade-in duration-500"
                                >
                                    {msg.role === "assistant" ? (
                                        <AssistantMessageItem
                                            msg={msg}
                                            isLatest={
                                                index === messages.length - 1
                                            }
                                            isLoading={isLoading}
                                        />
                                    ) : (
                                        <div className="flex flex-col items-end space-y-1.5 w-full min-w-0">
                                            <div className="flex items-center gap-2">
                                                <span className="text-[9px] font-medium text-muted-foreground/40 tabular-nums">
                                                    {new Date(
                                                        msg.timestamp
                                                    ).toLocaleTimeString([], {
                                                        hour: "2-digit",
                                                        minute: "2-digit",
                                                    })}
                                                </span>
                                                <span className="text-[10px] font-black text-primary/40 tracking-widest">
                                                    You
                                                </span>
                                            </div>
                                            <div className="bg-primary/5 border border-primary/20 p-4 rounded-2xl rounded-tr-none text-sm font-semibold max-w-[90%] text-primary leading-relaxed shadow-none break-all">
                                                <ReactMarkdown
                                                    remarkPlugins={[remarkGfm]}
                                                    components={
                                                        MarkdownComponents
                                                    }
                                                >
                                                    {msg.content}
                                                </ReactMarkdown>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </ScrollArea>

                    <div className="p-6 bg-background relative">
                        {showAgentMenu && (
                            <Card className="absolute bottom-full left-6 w-56 gap-0 bg-popover/95 backdrop-blur-2xl border-border shadow-2xl p-1 z-50 rounded-xl  animate-in slide-in-from-bottom-2">
                                <div className="px-2 py-1.5 text-[10px] font-black text-muted-foreground uppercase tracking-widest border-b border-border/50 mb-1">
                                    智能体
                                </div>
                                <div className="max-h-80 overflow-y-auto scrollbar-hide">
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
                                            <div className="flex flex-col min-w-0">
                                                <div
                                                    className={`text-[11px] font-bold transition-colors truncate ${
                                                        index === selectedIndex
                                                            ? "text-primary"
                                                            : "group-hover:text-primary"
                                                    }`}
                                                >
                                                    {agent.name}
                                                </div>
                                                <div className="text-[9px] text-muted-foreground/60 font-medium truncate">
                                                    {agent.role}
                                                </div>
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
                                disabled={!agents.some(a => a.identifier === "ceo_agent")}
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
                                    if (
                                        showAgentMenu &&
                                        filteredAgents.length > 0
                                    ) {
                                        if (e.key === "ArrowDown") {
                                            e.preventDefault();
                                            setSelectedIndex(
                                                (prev) =>
                                                    (prev + 1) %
                                                    filteredAgents.length
                                            );
                                            return;
                                        }
                                        if (e.key === "ArrowUp") {
                                            e.preventDefault();
                                            setSelectedIndex(
                                                (prev) =>
                                                    (prev -
                                                        1 +
                                                        filteredAgents.length) %
                                                    filteredAgents.length
                                            );
                                            return;
                                        }
                                        if (e.key === "Enter") {
                                            e.preventDefault();
                                            selectAgent(
                                                filteredAgents[selectedIndex]
                                            );
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
                                                                    placeholder={
                                                                        agents.some((a) => a.identifier === "ceo_agent")
                                                                            ? "输入指令或使用 @ 呼叫智能体..."
                                                                            : "正在连接智能体矩阵..."
                                                                    }
                                                                    className="w-full bg-transparent border-none focus:ring-0 p-3 text-sm font-medium resize-none min-h-[90px] outline-none placeholder:text-muted-foreground/30 leading-relaxed"
                                                                />                            <div className="flex items-center justify-between px-2 pb-1.5">
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
                                    disabled={!inputValue.trim() || isLoading || !agents.some(a => a.identifier === "ceo_agent")}
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
                                className="h-8 w-8 text-muted-foreground hover:text-background bg-primary/5 transition-colors"
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
                        {activeReport ? (
                            <ScrollArea className="flex-1 h-0 bg-background">
                                <div className="p-6 max-w-8xl mx-auto">
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
                                </div>
                            </ScrollArea>
                        ) : (
                            <div className="flex-1 flex flex-col items-center justify-center bg-background text-center space-y-8 opacity-30 grayscale mix-blend-luminosity">
                                <div className="relative">
                                    <div className="absolute inset-0 bg-primary/10 blur-[120px] rounded-full scale-150" />
                                    <div className="relative flex items-center justify-center">
                                        <Zap
                                            size={64}
                                            className="text-primary/40 animate-pulse"
                                        />
                                    </div>
                                </div>
                                <h3 className="text-4xl font-black uppercase tracking-[0.5em] italic text-muted-foreground/20">
                                    准备就绪
                                </h3>
                            </div>
                        )}
                    </div>
                </main>
            </div>
        </div>
    );
}
