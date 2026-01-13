import { useState, useEffect, useCallback } from 'react';
import { Node, Edge } from '@xyflow/react';
import { ENDPOINTS } from '@/lib/api';

interface BlueprintNode {
  id: string;
  task_name: string;
  capability: string;
  dependencies: string[];
}

interface Blueprint {
  nodes: BlueprintNode[];
}

interface NodeUpdate {
  id: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  output?: string;
}

export function useAgentControl(sessionId: string | null) {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [lastThought, setLastThought] = useState<string>('');
  const [status, setStatus] = useState<'idle' | 'connected' | 'error'>('idle');

  const processTopology = useCallback((blueprint: Blueprint) => {
    if (!blueprint.nodes || blueprint.nodes.length === 0) return;

    const newNodes: Node[] = blueprint.nodes.map((node, index) => {
      const isFirst = node.dependencies.length === 0;
      const isLast = !blueprint.nodes.some(n => n.dependencies.includes(node.id));
      
      return {
        id: node.id,
        data: { 
          label: node.task_name || (node as any).task || 'Unknown Task', 
          capability: node.capability,
          status: (node as any).status || 'PENDING',
          result: (node as any).output,
          isFirst,
          isLast
        },
        position: { x: index * 180 + 50, y: 150 }, // 水平排列布局
        type: 'agent', // 对应 workflow-graph 中的 nodeTypes 键名
      };
    });

    const newEdges: Edge[] = [];
    blueprint.nodes.forEach((node) => {
      node.dependencies.forEach((depId) => {
        newEdges.push({
          id: `e-${depId}-${node.id}`,
          source: depId,
          target: node.id,
          animated: true,
          style: { stroke: '#3b82f6' }
        });
      });
    });

    setNodes(newNodes);
    setEdges(newEdges);
  }, []);

  const updateNodeStatus = useCallback((nodeUpdates: NodeUpdate[]) => {
    setNodes((nds) =>
      nds.map((node) => {
        const update = nodeUpdates.find((u) => u.id === node.id);
        if (update) {
          return {
            ...node,
            data: {
              ...node.data,
              status: update.status,
              result: update.output
            },
          };
        }
        return node;
      })
    );
  }, []);

  useEffect(() => {
    if (!sessionId) return;

    const wsUrl = ENDPOINTS.WS_CONTROL_PANEL(sessionId);
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => setStatus('connected');
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case 'thought_emitted':
          setLastThought(data.payload.thought || '');
          break;
        case 'topology_update':
          processTopology(data.payload.blueprint);
          break;
        case 'execution_snapshot':
          updateNodeStatus(data.payload.nodes);
          break;
        case 'protocol_error':
          console.error('[Protocol Error]', data.payload.errors);
          break;
      }
    };

    ws.onerror = () => setStatus('error');
    ws.onclose = () => setStatus('idle');

    return () => ws.close();
  }, [sessionId, processTopology, updateNodeStatus]);

  return { nodes, edges, lastThought, status, setNodes, setEdges };
}