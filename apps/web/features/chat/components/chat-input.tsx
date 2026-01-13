"use client";

import { Button } from "@autonomy/ui/components/button";
import { Card } from "@autonomy/ui/components/card";
import { AtSign, Paperclip, Send, StopCircle } from "lucide-react";
import { useRef, useState } from "react";

interface Agent {
    id: string;
    identifier: string;
    name: string;
    role: string;
    avatar: string;
}

interface ChatInputProps {
    inputValue: string;
    setInputValue: (v: string) => void;
    isLoading: boolean;
    onSend: () => void;
    agents: Agent[];
}

export function ChatInput({
    inputValue,
    setInputValue,
    isLoading,
    onSend,
    agents,
}: ChatInputProps) {
    const [showAgentMenu, setShowAgentMenu] = useState(false);
    const [mentionQuery, setMentionQuery] = useState("");
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        const val = e.target.value;
        setInputValue(val);
        const lastAt = val.lastIndexOf("@");
        if (lastAt !== -1 && (lastAt === 0 || val[lastAt - 1] === " ")) {
            setShowAgentMenu(true);
            setMentionQuery(val.substring(lastAt + 1));
        } else {
            setShowAgentMenu(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            onSend();
        }
    };

    const selectAgent = (agent: Agent) => {
        const lastAt = inputValue.lastIndexOf("@");
        setInputValue(inputValue.substring(0, lastAt) + "@" + agent.name + " ");
        setShowAgentMenu(false);
        textareaRef.current?.focus();
    };

    return (
        <div className="p-6 bg-background relative">
            {showAgentMenu && (
                <Card className="absolute bottom-full left-6 w-56 bg-popover border p-1 z-50 rounded-xl mb-2">
                    {agents
                        .filter((a) =>
                            a.name
                                .toLowerCase()
                                .includes(mentionQuery.toLowerCase())
                        )
                        .map((agent) => (
                            <button
                                key={agent.id}
                                onClick={() => selectAgent(agent)}
                                className="w-full flex items-center gap-2.5 p-1.5 rounded-lg text-left hover:bg-primary/10"
                            >
                                <div className="w-6 h-6 rounded-md overflow-hidden bg-muted">
                                    <img
                                        src={agent.avatar}
                                        className="w-full h-full object-cover"
                                        alt={agent.name}
                                    />
                                </div>
                                <div className="flex flex-col min-w-0">
                                    <span className="text-[11px] font-bold truncate">
                                        {agent.name}
                                    </span>
                                    <span className="text-[9px] text-muted-foreground truncate">
                                        {agent.role}
                                    </span>
                                </div>
                            </button>
                        ))}
                </Card>
            )}

            <Card className="bg-background/50 border-border/40 p-1.5 flex flex-col gap-1 rounded-xl shadow-none">
                <textarea
                    ref={textareaRef}
                    value={inputValue}
                    onChange={handleInputChange}
                    onKeyDown={handleKeyDown}
                    placeholder="输入指令或使用 @ 呼叫智能体..."
                    className="w-full bg-transparent border-none p-3 text-sm font-medium resize-none min-h-[90px] outline-none"
                    disabled={isLoading}
                />
                <div className="flex items-center justify-between px-2 pb-1.5">
                    <div className="flex items-center gap-1">
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-muted-foreground"
                        >
                            <Paperclip size={16} />
                        </Button>
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-muted-foreground"
                            onClick={() => setShowAgentMenu(!showAgentMenu)}
                        >
                            <AtSign size={16} />
                        </Button>
                    </div>
                    <Button
                        size="icon"
                        disabled={!inputValue.trim() || isLoading}
                        onClick={onSend}
                        className="h-9 w-9 rounded-full bg-primary text-primary-foreground"
                    >
                        {isLoading ? (
                            <StopCircle size={16} className="animate-spin" />
                        ) : (
                            <Send size={16} />
                        )}
                    </Button>
                </div>
            </Card>
        </div>
    );
}
