"use client";

import {
    Controls,
    Edge,
    Node as FlowNode,
    Handle,
    NodeTypes,
    Position,
    ReactFlow,
    useEdgesState,
    useNodesState,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { Loader2, Zap } from "lucide-react";
import { useEffect, useMemo } from "react";

interface AgentNodeData extends Record<string, unknown> {
    name: string;
    role: string;
    avatar: string;
    status: "Idle" | "Thinking" | "Responding";
    isFirst: boolean;
    isLast: boolean;
}

const CustomNode = ({ data }: { data: AgentNodeData }) => {
    const isActive = data.status === "Thinking" || data.status === "Responding";

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
                        isActive
                            ? "border-primary ring-4 ring-primary/10"
                            : "border-border/70 hover:border-primary"
                    }`}
                >
                    {data.avatar ? (
                        <img
                            src={data.avatar}
                            alt={data.name}
                            className="w-full h-full object-cover"
                        />
                    ) : (
                        <div className="w-full h-full flex items-center justify-center bg-primary/5 text-sm font-bold">
                            {data.name?.charAt(0)}
                        </div>
                    )}
                </div>

                {isActive && (
                    <div className="absolute inset-0 bg-primary/30 backdrop-blur-[1px] rounded-[11px] flex items-center justify-center animate-in fade-in duration-300">
                        <Loader2
                            size={16}
                            className="text-white/90 animate-spin"
                        />
                    </div>
                )}
            </div>

            <div
                className={`text-xs tracking-wide text-center transition-colors max-w-[60px] truncate ${
                    isActive
                        ? "text-primary/80"
                        : "text-muted-foreground/50 group-hover:text-muted-foreground/80"
                }`}
            >
                {data.name}
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

interface ExecutionWorkflowProps {
    workflowSteps: {
        agentId: string;
        agentName: string;
        agentRole: string;
        agentAvatar: string;
        status: "Idle" | "Thinking" | "Responding";
        parentId?: string;
    }[];
}

export function ExecutionWorkflow({ workflowSteps }: ExecutionWorkflowProps) {
    const [nodes, setNodes, onNodesChange] = useNodesState<FlowNode>([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

    const nodeTypes: NodeTypes = useMemo(
        () => ({
            agent: CustomNode,
        }),
        []
    );

    useEffect(() => {
        if (workflowSteps.length === 0) {
            setNodes([]);
            setEdges([]);
            return;
        }

        // --- Simplified Tree Layout Algorithm ---
        const nodeMap = new Map<string, typeof workflowSteps[0]>();
        workflowSteps.forEach(s => nodeMap.set(s.agentId, s));

        // 1. Calculate depths
        const depths: Record<string, number> = {};
        const getDepth = (id: string): number => {
            if (depths[id] !== undefined) return depths[id];
            const step = nodeMap.get(id);
            if (!step || !step.parentId || !nodeMap.has(step.parentId)) {
                depths[id] = 0;
                return 0;
            }
            const d = 1 + getDepth(step.parentId);
            depths[id] = d;
            return d;
        };
        workflowSteps.forEach(s => getDepth(s.agentId));

        // 2. Group by depth for vertical positioning
        const levelGroups: Record<number, string[]> = {};
        workflowSteps.forEach(s => {
            const d = depths[s.agentId];
            if (!levelGroups[d]) levelGroups[d] = [];
            levelGroups[d].push(s.agentId);
        });

        // 3. Create Nodes with calculated positions
        const xSpacing = 180;
        const ySpacing = 100;

        const newNodes: FlowNode[] = workflowSteps.map((step) => {
            const depth = depths[step.agentId];
            const indexInLevel = levelGroups[depth].indexOf(step.agentId);
            const levelSize = levelGroups[depth].length;
            
            // Vertical centering logic
            const yOffset = (indexInLevel - (levelSize - 1) / 2) * ySpacing;

            return {
                id: step.agentId,
                type: "agent",
                position: { 
                    x: depth * xSpacing + 50, 
                    y: 150 + yOffset 
                },
                data: {
                    name: step.agentName,
                    role: step.agentRole,
                    avatar: step.agentAvatar,
                    status: step.status,
                    isFirst: depth === 0,
                    isLast: !workflowSteps.some(s => s.parentId === step.agentId),
                },
            };
        });

        const newEdges: Edge[] = [];
        workflowSteps.forEach((step) => {
            if (step.parentId && nodeMap.has(step.parentId)) {
                newEdges.push({
                    id: `e-${step.parentId}-${step.agentId}`,
                    source: step.parentId,
                    target: step.agentId,
                    animated:
                        workflowSteps.find((s) => s.agentId === step.parentId)
                            ?.status !== "Idle" || step.status !== "Idle",
                    type: "smoothstep",
                    style: {
                        stroke: "var(--primary)",
                        strokeWidth: 1.5,
                        opacity: 0.15,
                    },
                });
            }
        });

        setNodes(newNodes);
        setEdges(newEdges);
    }, [workflowSteps, setNodes, setEdges]);

    return (
        <div className="w-full h-full bg-muted/5 bg-linear-to-br from-transparent to-primary/10">
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                nodeTypes={nodeTypes}
                fitView
                fitViewOptions={{ padding: 2.5 }}
                minZoom={0.1}
                maxZoom={1.5}
                defaultViewport={{ zoom: 0.4, x: 0, y: 0 }}
            >
                <Controls showInteractive={false} className="!bg-background !border-border/40 !shadow-none opacity-20 hover:opacity-100 transition-opacity" />
            </ReactFlow>
        </div>
    );
}

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
