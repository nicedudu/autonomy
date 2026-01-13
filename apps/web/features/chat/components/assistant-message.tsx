"use client";

import { Zap } from "lucide-react";
import { useMemo } from "react";
import { MarkdownRenderer } from "./markdown-renderer";
import { parseProtocol } from "@/lib/stream-parser";
import { ThoughtWidget } from "./thought-widget";
import { PlanWidget } from "./plan-widget";

interface MessageType {
    id: string;
    role: "user" | "assistant";
    content: string;
    agent_id?: string;
    agent_name?: string;
    agent_avatar?: string;
    timestamp: number;
    status?: string;
}

interface AssistantMessageProps {
    msg: MessageType;
    isLatest: boolean;
    isLoading: boolean;
}

export function AssistantMessage({
    msg,
    isLatest,
    isLoading,
}: AssistantMessageProps) {
    const content = msg.content || "";
    const isStreaming = isLatest && isLoading;

    const { thought, plan, content: displayContent, isThoughtClosed, isPlanClosed } = useMemo(() => {
        return parseProtocol(content);
    }, [content]);

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
                {msg.timestamp && (
                    <span className="text-[9px] font-medium text-muted-foreground/50 tabular-nums">
                        {new Date(msg.timestamp).toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                        })}
                    </span>
                )}
            </div>

            {/* --- 前置等待动画 --- */}
            {isStreaming && !displayContent && !thought && !plan && (
                <div className="flex gap-1.5 items-center p-2 animate-in fade-in duration-300">
                    <span className="w-1.5 h-1.5 rounded-full bg-primary/40 animate-bounce animation-duration-[0.8s] [animation-delay:-0.3s]"></span>
                    <span className="w-1.5 h-1.5 rounded-full bg-primary/40 animate-bounce animation-duration-[0.8s] [animation-delay:-0.15s]"></span>
                    <span className="w-1.5 h-1.5 rounded-full bg-primary/40 animate-bounce animation-duration-[0.8s]"></span>
                </div>
            )}

            {thought && (
                <ThoughtWidget thought={thought} isClosed={isThoughtClosed} />
            )}

            {plan && (
                <PlanWidget plan={plan} isClosed={isPlanClosed} />
            )}

            {displayContent && (
                <div className="text-sm leading-relaxed text-foreground/90 font-medium relative [&_p]:mb-6 last:[&_p]:mb-0 break-all w-full min-w-0">
                    <MarkdownRenderer content={displayContent} />
                </div>
            )}

            {isLatest && isLoading && msg.status && (
                <div className="flex items-center gap-1.5 px-2 py-0.5 bg-primary/5 border border-primary/10 rounded-full w-fit animate-in fade-in zoom-in-95 mt-1.5 shadow-sm">
                    <Zap size={10} className="text-primary animate-pulse" />
                    <span className="text-[9px] font-black text-primary/80 tracking-tight uppercase">
                        {msg.status}
                    </span>
                </div>
            )}
        </div>
    );
}
