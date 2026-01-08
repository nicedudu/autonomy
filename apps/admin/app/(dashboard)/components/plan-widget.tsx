import { PlanStep } from "@/lib/stream-parser";
import { CheckCircle, Circle, Clock, Loader2, XCircle } from "lucide-react";
import { cn } from "@autonomy/ui/lib/utils";

interface PlanWidgetProps {
  plan: PlanStep[] | null;
  className?: string;
}

export function PlanWidget({ plan, className }: PlanWidgetProps) {
  // Defensive check: If plan is null, undefined, or empty array, don't render
  if (!plan || !Array.isArray(plan) || plan.length === 0) return null;

  return (
    <div className={cn("w-64 border-l bg-muted/10 p-4 h-full overflow-y-auto hidden md:block", className)}>
      <h3 className="font-semibold mb-4 text-sm uppercase tracking-wider text-muted-foreground">Execution Plan</h3>
      <div className="space-y-4">
        {plan.map((step, idx) => (
          <div key={idx} className="flex gap-3 text-sm">
            <div className="mt-0.5 shrink-0">
              {step.state === "completed" && <CheckCircle className="w-4 h-4 text-green-500" />}
              {step.state === "in_progress" && <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />}
              {step.state === "no_started" && <Circle className="w-4 h-4 text-muted-foreground" />}
              {step.state === "blocked" && <XCircle className="w-4 h-4 text-red-500" />}
            </div>
            <div className={cn(
              "leading-tight",
              step.state === "completed" && "text-muted-foreground line-through",
              step.state === "in_progress" && "font-medium text-foreground",
              step.state === "no_started" && "text-muted-foreground"
            )}>
              {step.step}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
