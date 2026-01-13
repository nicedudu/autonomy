
import React from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  NodeTypes,
  Node,
  Edge,
  OnNodesChange,
  OnEdgesChange,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { AgentNode } from './agent-node';

const nodeTypes: NodeTypes = {
  agent: AgentNode,
};

interface WorkflowGraphProps {
  nodes: Node[];
  edges: Edge[];
  onNodesChange?: OnNodesChange;
  onEdgesChange?: OnEdgesChange;
}

export const WorkflowGraph = ({ nodes, edges, onNodesChange, onEdgesChange }: WorkflowGraphProps) => {
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
        <Controls 
          showInteractive={false} 
          className="!bg-background !border-border/40 !shadow-none opacity-20 hover:opacity-100 transition-opacity" 
        />
      </ReactFlow>
    </div>
  );
};
