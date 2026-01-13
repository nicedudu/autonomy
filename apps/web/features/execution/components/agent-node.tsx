import React from 'react';
import { Handle, Position } from '@xyflow/react';
import { Loader2 } from 'lucide-react';

interface AgentNodeData {
    label: string; // 对应原本的 name
    capability: string;
    status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
    result?: string;
    isFirst?: boolean;
    isLast?: boolean;
}

export const AgentNode = ({ data }: { data: AgentNodeData }) => {
    // 映射状态到原始样式的活跃判断
    const isActive = data.status === 'RUNNING';
    const isCompleted = data.status === 'COMPLETED';
    const isFailed = data.status === 'FAILED';

    // 图像逻辑还原 (Dicebear 兜底)
    const avatarUrl = `https://api.dicebear.com/7.x/bottts/svg?seed=${data.label}`;

    return (
        <div className="group relative flex flex-col items-center gap-1 cursor-pointer">
            {!data.isFirst && (
                <Handle
                    type="target"
                    position={Position.Left}
                    className="!bg-primary !border-none !w-0 !h-0 !opacity-0"
                    style={{ top: "24px" }}
                />
            )}

            <div className="relative">
                <div
                    className={`w-12 h-12 rounded-xl bg-background border-2 overflow-hidden transition-all duration-300 shadow-sm ${
                        isActive || isCompleted
                            ? "border-primary ring-4 ring-primary/10"
                            : isFailed 
                            ? "border-red-500" 
                            : "border-border/70 hover:border-primary"
                    }`}
                >
                    <img
                        src={avatarUrl}
                        alt={data.label}
                        className="w-full h-full object-cover"
                    />
                </div>

                {isActive && (
                    <div className="absolute inset-0 bg-primary/30 backdrop-blur-[1px] rounded-[11px] flex items-center justify-center animate-in fade-in duration-300">
                        <Loader2
                            size={16}
                            className="text-white/90 animate-spin"
                        />
                    </div>
                )}
                
                {isCompleted && (
                    <div className="absolute -top-1 -right-1 bg-green-500 rounded-full p-0.5 border-2 border-white">
                        <div className="w-1.5 h-1.5 bg-white rounded-full" />
                    </div>
                )}
            </div>

            <div
                className={`text-[10px] font-bold tracking-wide text-center transition-colors max-w-[80px] truncate ${
                    isActive
                        ? "text-primary/80"
                        : "text-muted-foreground/50 group-hover:text-muted-foreground/80"
                }`}
            >
                {data.label}
            </div>

            {!data.isLast && (
                <Handle
                    type="source"
                    position={Position.Right}
                    className="!bg-primary !border-none !w-0 !h-0 !opacity-0"
                    style={{ top: "24px" }}
                />
            )}
        </div>
    );
};