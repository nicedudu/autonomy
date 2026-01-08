"use client";

import { 
    Brain, 
    ChevronDown, 
    ChevronRight
} from "lucide-react";
import { useState } from "react";
import { MarkdownRenderer } from "./MarkdownRenderer";

interface ThoughtWidgetProps {
    thought: string;
    isClosed: boolean;
}

export function ThoughtWidget({ thought, isClosed }: ThoughtWidgetProps) {
    const [isExpanded, setIsExpanded] = useState(false);
    const [isHovered, setIsHovered] = useState(false);

    return (
        <div
            className={`rounded-xl overflow-hidden transition-all w-full min-w-0 border ${
                isExpanded
                    ? "bg-muted/30 border-border/40"
                    : "bg-transparent border-transparent"
            }`}
        >
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                onMouseEnter={() => setIsHovered(true)}
                onMouseLeave={() => setIsHovered(false)}
                className="flex items-center gap-2 px-1.5 py-1.5 hover:text-foreground/80 transition-colors text-[10px] font-bold text-muted-foreground/70 tracking-tight"
            >
                <div className="w-4 h-4 flex items-center justify-center">
                    {isHovered ? (
                        isExpanded ? (
                            <ChevronDown size={14} />
                        ) : (
                            <ChevronRight size={14} />
                        )
                    ) : (
                        <Brain
                            size={14}
                            className="text-primary/60 animate-pulse"
                        />
                    )}
                </div>
                <span>
                    {isClosed ? "深度思考" : "深度思考中..."}
                </span>
            </button>
            {isExpanded && (
                <div className="px-4 pb-3 text-xs leading-relaxed text-muted-foreground/60 italic font-medium border-t border-border/20 pt-2 break-all">
                    <MarkdownRenderer content={thought} compact />
                </div>
            )}
        </div>
    );
}
