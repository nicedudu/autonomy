"use client";

import { Button } from "@autonomy/ui/components/button";
import { ChevronDown, Sparkles } from "lucide-react";
import { RefObject } from "react";
import { AssistantMessage } from "./AssistantMessage";

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

interface MessageListProps {
    messages: MessageType[];
    isLoading: boolean;
    viewportRef: RefObject<HTMLDivElement | null>;
    onScroll: (e: React.UIEvent<HTMLDivElement>) => void;
    showScrollButton: boolean;
    hasNewMessages: boolean;
    onScrollToBottom: () => void;
}

export function MessageList({
    messages,
    isLoading,
    viewportRef,
    onScroll,
    showScrollButton,
    hasNewMessages,
    onScrollToBottom,
}: MessageListProps) {
    // We need to pass the ref to the viewport element of the ScrollArea,
    // but the shadcn ScrollArea component encapsulates it. 
    // So we'll use a standard div with overflow for now to maintain direct ref control 
    // which is crucial for the scrolling logic passed from parent.
    
    return (
        <div className="flex-1 min-h-0 relative flex flex-col bg-muted/5">
            <div 
                ref={viewportRef}
                onScroll={onScroll}
                className="flex-1 overflow-y-auto w-full scroll-smooth"
            >
                <div className="p-6 space-y-8 pb-12 min-h-full">
                    {messages.length === 0 && (
                        <div className="space-y-4">
                            <div className="flex items-center gap-3 text-primary">
                                <Sparkles size={20} />
                                <h3 className="text-sm font-bold uppercase">
                                    就绪
                                </h3>
                            </div>
                            <p className="text-xs font-medium text-muted-foreground">
                                请输入指令启动策略分析。
                            </p>
                        </div>
                    )}
                    {messages.map((msg, index) => (
                        <div key={msg.id} className="w-full">
                            {msg.role === "assistant" ? (
                                <AssistantMessage
                                    msg={msg}
                                    isLatest={index === messages.length - 1}
                                    isLoading={isLoading}
                                />
                            ) : (
                                <div className="flex justify-end w-full pl-12">
                                    <div className="flex flex-col items-end space-y-1.5 max-w-full">
                                        <span className="text-[10px] font-black text-primary/40 mr-1">
                                            You
                                        </span>
                                        <div className="bg-primary/5 border border-primary/20 p-4 rounded-2xl rounded-tr-none text-sm font-semibold text-primary break-words w-fit">
                                            {msg.content}
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>

            {showScrollButton && (
                <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-50">
                    <Button
                        size="sm"
                        onClick={onScrollToBottom}
                        className="rounded-full bg-primary text-primary-foreground text-[10px] font-bold gap-2 h-9 px-4"
                    >
                        {hasNewMessages ? (
                            <Sparkles
                                size={14}
                                className="fill-current"
                            />
                        ) : (
                            <ChevronDown size={14} />
                        )}
                        <span>
                            {hasNewMessages
                                ? "查看新消息"
                                : "回到最底部"}
                        </span>
                    </Button>
                </div>
            )}
        </div>
    );
}
