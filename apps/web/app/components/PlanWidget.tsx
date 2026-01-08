"use client";

import { 
    CheckCircle2, 
    Circle, 
    PlayCircle, 
    XCircle,
    ClipboardList,
    ChevronDown,
    ChevronRight,
    Loader2
} from "lucide-react";
import { useState } from "react";
import { PlanStep } from "@/lib/stream-parser";

interface PlanWidgetProps {
    plan: PlanStep[];
    isClosed: boolean;
}

export function PlanWidget({ plan, isClosed }: PlanWidgetProps) {
    const [isExpanded, setIsExpanded] = useState(true);
    const [isHovered, setIsHovered] = useState(false);

    const getPlanIcon = (state: PlanStep["state"]) => {
        switch (state) {
            case "completed":
                return <CheckCircle2 size={14} className="text-green-500/80" />;
            case "in_progress":
                return <Loader2 size={14} className="text-primary animate-spin" />;
            case "blocked":
                return <XCircle size={14} className="text-destructive/80" />;
            default:
                return <Circle size={14} className="text-muted-foreground/30" />;
        }
    };

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
                        <ClipboardList
                            size={14}
                            className="text-primary/60"
                        />
                    )}
                </div>
                <span>
                    {isClosed ? "执行计划" : "生成计划中..."}
                </span>
            </button>
            {isExpanded && (
                <div className="px-4 pb-3 space-y-2 border-t border-border/20 pt-3">
                    {plan.map((step, idx) => (
                        <div key={idx} className="flex items-start gap-3">
                            <div className="mt-0.5 shrink-0">
                                {getPlanIcon(step.state)}
                            </div>
                            <div className={`text-[11px] font-medium leading-relaxed ${
                                step.state === 'completed' ? 'text-muted-foreground/40 line-through decoration-muted-foreground/20' : 'text-muted-foreground/80'
                            }`}>
                                {step.step}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
