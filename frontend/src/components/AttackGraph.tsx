import React, { useMemo } from 'react';
import { ReactFlow, MiniMap, Controls, Background, MarkerType, Node, Edge } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

interface LogEntry {
  hypothesis: string;
  policy: { status: string; reason: string };
  execution: { status: string; output: string };
}

interface AttackGraphProps {
  logs: LogEntry[];
  target: string;
}

export default function AttackGraph({ logs, target }: AttackGraphProps) {
  
  const { nodes, edges } = useMemo(() => {
    const initialNodes: Node[] = [
      {
        id: 'start',
        position: { x: 250, y: 50 },
        data: { label: `Target: ${target}` },
        style: { background: '#2563eb', color: 'white', fontWeight: 'bold', borderRadius: '8px' }
      }
    ];
    const initialEdges: Edge[] = [];

    logs.forEach((log, index) => {
      const nodeId = `log-${index}`;
      const prevNodeId = index === 0 ? 'start' : `log-${index - 1}`;
      
      const isApproved = log.policy.status === 'APPROVED';
      const bgColor = isApproved ? '#059669' : '#dc2626';

      // Keep label concise
      const label = isApproved 
        ? `Action ${index + 1}\n\n${log.execution.output?.substring(0, 50)}...`
        : `BLOCKED\n${log.policy.reason}`;

      initialNodes.push({
        id: nodeId,
        position: { x: 250, y: 50 + (index + 1) * 150 },
        data: { label: label },
        style: { background: bgColor, color: 'white', borderRadius: '8px', padding: '10px', width: 200 }
      });

      initialEdges.push({
        id: `e-${prevNodeId}-${nodeId}`,
        source: prevNodeId,
        target: nodeId,
        animated: true,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#cbd5e1',
        },
        style: { stroke: '#cbd5e1' }
      });
    });

    return { nodes: initialNodes, edges: initialEdges };
  }, [logs, target]);

  return (
    <div style={{ width: '100%', height: '500px', background: '#0f172a', borderRadius: '12px', overflow: 'hidden' }}>
      <ReactFlow nodes={nodes} edges={edges} fitView>
        <MiniMap nodeStrokeColor="#ffffff" nodeColor="#1e293b" maskColor="rgba(0,0,0,0.5)" />
        <Controls />
        <Background color="#334155" gap={16} />
      </ReactFlow>
    </div>
  );
}
