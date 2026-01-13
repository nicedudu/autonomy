"use client";

import { 
    ChevronDown, 
    ListChecks,
    Circle,
    CheckCircle2,
    Loader2
} from "lucide-react";
import { useState } from "react";

interface PlanStep {
    step: string;
    state: "not_started" | "in_progress" | "completed" | "blocked";
}

interface PlanWidgetProps {
    plan: PlanStep[];
    isClosed: boolean;
}

export function PlanWidget({ plan, isClosed }: PlanWidgetProps) {
    const [isExpanded, setIsExpanded] = useState(true);

    if (!plan || plan.length === 0) return null;

    return (
        <div className="bg-primary/5 border border-primary/10 rounded-xl p-4 my-4 animate-in fade-in zoom-in-95 duration-500">
            <div 
                className="flex items-center justify-between cursor-pointer select-none mb-3"
                onClick={() => setIsExpanded(!isExpanded)}
            >
                <div className="flex items-center gap-2.5">
                    <div className="w-6 h-6 rounded-lg bg-primary/10 flex items-center justify-center">
                        <ListChecks size={14} className="text-primary" />
                    </div>
                    <span className="text-[11px] font-black uppercase tracking-tighter text-primary/80">
                        执行方案 (SOP)
                    </span>
                    
                    {/* --- 生成中的跳动动画 --- */}
                    {!isClosed && (
                        <div className="flex gap-1 items-center">
                            <span className="w-1 h-1 rounded-full bg-primary/40 animate-bounce [animation-duration:0.8s] [animation-delay:-0.3s]"></span>
                            <span className="w-1 h-1 rounded-full bg-primary/40 animate-bounce [animation-duration:0.8s] [animation-delay:-0.15s]"></span>
                            <span className="w-1 h-1 rounded-full bg-primary/40 animate-bounce [animation-duration:0.8s]"></span>
                        </div>
                    )}
                </div>
                <ChevronDown 
                    size={14} 
                    className={`text-primary/40 transition-transform duration-300 ${isExpanded ? "" : "-rotate-90"}`} 
                />
            </div>

            {isExpanded && (
                <div className="space-y-2.5">
                    {plan.map((step, idx) => (
                        <div key={idx} className="flex items-start gap-3 group">
                            <div className="mt-1 flex-shrink-0">
                                {step.state === "completed" ? (
                                    <CheckCircle2 size={14} className="text-green-500" />
                                ) : step.state === "in_progress" ? (
                                    <Loader2 size={14} className="text-primary animate-spin" />
                                ) : (
                                    <Circle size={14} className="text-primary/20" />
                                )}
                            </div>
                            <span className={`text-[12px] font-semibold leading-tight ${
                                step.state === "completed" ? "text-muted-foreground/50 line-through" : "text-foreground/80"
                            }`}>
                                {step.step}
                            </span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}