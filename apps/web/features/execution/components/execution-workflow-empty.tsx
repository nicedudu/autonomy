import React from 'react';
import { Zap } from 'lucide-react';

export function ExecutionWorkflowEmpty() {
    return (
        <div className="w-full h-full p-8 flex flex-col items-center justify-center bg-muted/5 bg-linear-to-br from-transparent to-primary/10">
            <div className="flex flex-col items-center justify-center opacity-10 grayscale select-none">
                <Zap size={48} strokeWidth={1} className="animate-pulse" />
                <h3 className="text-[10px] font-black tracking-[0.3em] uppercase mt-4">
                    System Ready
                </h3>
            </div>
        </div>
    );
}