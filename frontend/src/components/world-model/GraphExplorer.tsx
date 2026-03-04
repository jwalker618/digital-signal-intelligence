"use client";

import { useEffect, useState, useRef, useMemo } from 'react';
import dynamic from 'next/dynamic';

// Dynamically import the force graph so it doesn't crash Next.js SSR
const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { 
  ssr: false,
  loading: () => <div className="flex h-full items-center justify-center text-slate-500">Loading physics engine...</div>
});

export default function WorldModelGraph({ submission }: { submission: any }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  // Auto-resize the graph to fit the container
  useEffect(() => {
    if (containerRef.current) {
      setDimensions({
        width: containerRef.current.clientWidth,
        height: containerRef.current.clientHeight
      });
    }
  }, [submission]);

  // Parse the active submission into Nodes and Links
  const graphData = useMemo(() => {
    if (!submission) return { nodes: [], links: [] };

    const nodes: any[] = [];
    const links: any[] = [];
    const groups = new Set<string>();

    const entityName = submission.entity_name || "Unknown Entity";
    
    // 1. Create the Central Hub Node (The Company)
    nodes.push({ id: 'hub', name: entityName, val: 30, color: '#3b82f6' }); // Blue

    // Extract signals. The seed script populated these with group_id and signal_id!
    const signals = submission.model_versions?.[0]?.signal_conditions || [];
    const parsedSignals = typeof signals === 'string' ? JSON.parse(signals) : signals;

    parsedSignals.forEach((sig: any) => {
      // 2. Create Group Nodes (e.g., "technical_infrastructure")
      const groupId = sig.group_id || "general";
      if (!groups.has(groupId)) {
        groups.add(groupId);
        nodes.push({ id: groupId, name: groupId.replace('_', ' ').toUpperCase(), val: 15, color: '#8b5cf6' }); // Purple
        links.push({ source: 'hub', target: groupId });
      }

      // 3. Create Signal Leaf Nodes (e.g., "tls_configuration")
      const signalId = sig.signal_id || Math.random().toString();
      const isNegative = sig.action === "refer" || sig.action === "flag";
      
      nodes.push({ 
        id: signalId, 
        name: sig.note || signalId, 
        val: 5, 
        color: isNegative ? '#ef4444' : '#10b981' // Red if bad, Green if good
      });
      links.push({ source: groupId, target: signalId });
    });

    return { nodes, links };
  }, [submission]);

  return (
    <div ref={containerRef} className="w-full h-full min-h-[500px] bg-slate-950 rounded-lg border border-slate-800 overflow-hidden cursor-move">
      {graphData.nodes.length > 0 ? (
        <ForceGraph2D
          width={dimensions.width}
          height={dimensions.height}
          graphData={graphData}
          nodeLabel="name"
          nodeColor={(node: any) => node.color}
          nodeRelSize={1}
          linkColor={() => '#334155'} // slate-700
          linkWidth={2}
          d3VelocityDecay={0.3}
        />
      ) : (
        <div className="flex h-full items-center justify-center text-slate-500">No signals found to map.</div>
      )}
    </div>
  );
}