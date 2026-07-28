import React, { useState, useEffect, useRef, useCallback } from 'react';
import ForceGraph3D from 'react-force-graph-3d';
import axios from 'axios';
import { Layers, Box, Workflow, Loader2, Code, Zap, X, Cpu, FileText } from 'lucide-react';

const API_BASE = 'http://localhost:3333/api';

export default function App() {
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState('');
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(false);
  const [selectedNode, setSelectedNode] = useState(null);
  const [compiledContext, setCompiledContext] = useState(null);
  const [compiling, setCompiling] = useState(false);
  const fgRef = useRef();

  useEffect(() => {
    axios.get(`${API_BASE}/projects`).then(res => {
      setProjects(res.data.projects);
      if (res.data.projects.length > 0) {
        setSelectedProject(res.data.projects[0]);
      }
    }).catch(err => console.error("Failed to load projects", err));
  }, []);

  useEffect(() => {
    if (!selectedProject) return;
    setLoading(true);
    setSelectedNode(null);
    setCompiledContext(null);

    axios.get(`${API_BASE}/graph/${selectedProject}`).then(res => {
      const g = res.data.graph;
      const parsedData = {
        nodes: g.nodes.map(n => ({
          ...n,
          id: n.id,
          name: n.label || n.id,
          val: (n.degree || 1) * 0.5,
          color: res.data.communities[n.community] ? getColorForCommunity(n.community) : '#a855f7'
        })),
        links: (g.edges || g.links || []).map(e => ({
          ...e,
          source: e.source,
          target: e.target
        }))
      };
      setGraphData(parsedData);
      setLoading(false);
      
      setTimeout(() => {
        if (fgRef.current) fgRef.current.zoomToFit(1000, 50);
      }, 1000);
      
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, [selectedProject]);

  const handleNodeClick = useCallback((node) => {
    setSelectedNode(node);
    setCompiling(true);
    axios.get(`${API_BASE}/compile/${selectedProject}?node=${encodeURIComponent(node.name || node.id)}&compress=true`)
      .then(res => {
        setCompiledContext(res.data);
        setCompiling(false);
      })
      .catch(err => {
        console.error("Context compile error", err);
        setCompiledContext({ markdown_context: "⚠️ Could not slice code AST for this node." });
        setCompiling(false);
      });
  }, [selectedProject]);

  const getColorForCommunity = useCallback((cid) => {
    const colors = ["#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231", "#911eb4", "#46f0f0", "#f032e6", "#bcf60c", "#fabebe", "#008080", "#e6beff", "#9a6324", "#fffac8", "#800000", "#aaffc3", "#808000", "#ffd8b1", "#000075", "#808080", "#ffffff"];
    return colors[Math.abs(hashString(String(cid))) % colors.length];
  }, []);

  const hashString = (str) => {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    return hash;
  };

  return (
    <div style={{ width: '100vw', height: '100vh', margin: 0, padding: 0, backgroundColor: '#020202', color: 'white', fontFamily: 'Inter, sans-serif', overflow: 'hidden' }}>
      
      {/* Header Overlay */}
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, padding: '20px', zIndex: 10, display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'linear-gradient(to bottom, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0) 100%)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <div style={{ background: 'rgba(168, 85, 247, 0.2)', padding: '10px', borderRadius: '12px', backdropFilter: 'blur(10px)', border: '1px solid rgba(168, 85, 247, 0.4)' }}>
            <Layers color="#a855f7" size={24} />
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: '20px', fontWeight: '600', letterSpacing: '-0.5px' }}>Antigravity Graph Engine</h1>
            <p style={{ margin: 0, fontSize: '12px', color: '#9ca3af' }}>AST Context Compiler Protocol v2.0</p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <select 
            value={selectedProject} 
            onChange={(e) => setSelectedProject(e.target.value)}
            style={{ 
              backgroundColor: 'rgba(255,255,255,0.08)', 
              color: 'white', 
              border: '1px solid rgba(255,255,255,0.15)', 
              borderRadius: '8px', 
              padding: '8px 16px',
              outline: 'none',
              cursor: 'pointer',
              backdropFilter: 'blur(10px)'
            }}
          >
            {projects.map(p => <option key={p} value={p} style={{background: '#111'}}>{p}</option>)}
          </select>
        </div>
      </div>

      {/* Info Panel Overlay */}
      <div style={{ position: 'absolute', bottom: '20px', left: '20px', zIndex: 10, display: 'flex', gap: '10px' }}>
        <div style={{ background: 'rgba(255,255,255,0.05)', padding: '10px 16px', borderRadius: '10px', backdropFilter: 'blur(10px)', border: '1px solid rgba(255,255,255,0.08)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Box size={16} color="#4ade80" />
          <span style={{ fontSize: '13px', fontWeight: 500 }}>{graphData.nodes.length.toLocaleString()} Nodes</span>
        </div>
        <div style={{ background: 'rgba(255,255,255,0.05)', padding: '10px 16px', borderRadius: '10px', backdropFilter: 'blur(10px)', border: '1px solid rgba(255,255,255,0.08)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Workflow size={16} color="#60a5fa" />
          <span style={{ fontSize: '13px', fontWeight: 500 }}>{graphData.links.length.toLocaleString()} Edges</span>
        </div>
      </div>

      {/* Node Inspector Drawer */}
      {selectedNode && (
        <div style={{ 
          position: 'absolute', top: '80px', right: '20px', bottom: '20px', width: '420px', 
          backgroundColor: 'rgba(10, 10, 15, 0.92)', backdropFilter: 'blur(16px)', 
          border: '1px solid rgba(255,255,255,0.12)', borderRadius: '16px', zIndex: 30, 
          display: 'flex', flexDirection: 'column', padding: '20px', overflow: 'hidden'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Cpu size={18} color="#a855f7" />
              <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600 }}>AST Node Inspector</h3>
            </div>
            <button onClick={() => setSelectedNode(null)} style={{ background: 'none', border: 'none', color: '#9ca3af', cursor: 'pointer' }}>
              <X size={20} />
            </button>
          </div>

          <div style={{ marginBottom: '12px' }}>
            <div style={{ fontSize: '18px', fontWeight: 700, color: '#f3f4f6' }}>{selectedNode.name}</div>
            <div style={{ fontSize: '12px', color: '#9ca3af', marginTop: '4px' }}>Community: {selectedNode.community || 'General'}</div>
          </div>

          {/* Token Compression Metrics Pill */}
          {compiledContext?.metrics && (
            <div style={{ 
              background: 'linear-gradient(135deg, rgba(168,85,247,0.15), rgba(59,130,246,0.15))', 
              border: '1px solid rgba(168,85,247,0.3)', borderRadius: '12px', padding: '12px', 
              marginBottom: '16px', display: 'flex', justifyContent: 'space-around', textAlign: 'center' 
            }}>
              <div>
                <div style={{ fontSize: '11px', color: '#9ca3af' }}>Raw Tokens</div>
                <div style={{ fontSize: '15px', fontWeight: 700, color: '#ef4444' }}>{compiledContext.metrics.raw_estimated_tokens}</div>
              </div>
              <div>
                <div style={{ fontSize: '11px', color: '#9ca3af' }}>Compressed</div>
                <div style={{ fontSize: '15px', fontWeight: 700, color: '#10b981' }}>{compiledContext.metrics.compressed_tokens}</div>
              </div>
              <div>
                <div style={{ fontSize: '11px', color: '#9ca3af' }}>Savings</div>
                <div style={{ fontSize: '15px', fontWeight: 700, color: '#a855f7', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '2px' }}>
                  <Zap size={14} /> {compiledContext.metrics.compression_savings_percent}
                </div>
              </div>
            </div>
          )}

          {/* Code Context Display */}
          <div style={{ flex: 1, overflowY: 'auto', backgroundColor: '#050508', borderRadius: '10px', padding: '14px', border: '1px solid rgba(255,255,255,0.05)', fontSize: '12px', fontFamily: 'monospace', whiteSpace: 'pre-wrap', color: '#d1d5db' }}>
            {compiling ? (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '8px', color: '#a855f7' }}>
                <Loader2 className="lucide-spin" size={20} /> Slicing AST Code...
              </div>
            ) : (
              compiledContext?.markdown_context || 'No code context available.'
            )}
          </div>
        </div>
      )}

      {loading && (
        <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', zIndex: 20, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
          <Loader2 className="lucide-spin" size={48} color="#a855f7" />
          <div style={{ color: '#a855f7', fontWeight: 500 }}>Rendering Graph Canvas...</div>
        </div>
      )}

      {/* WebGL Canvas */}
      {!loading && graphData.nodes.length > 0 && (
        <ForceGraph3D
          ref={fgRef}
          graphData={graphData}
          nodeId="id"
          nodeColor="color"
          nodeLabel="name"
          nodeRelSize={4}
          linkWidth={0.5}
          linkColor={() => 'rgba(255,255,255,0.12)'}
          backgroundColor="#020202"
          showNavInfo={false}
          warmupTicks={100}
          cooldownTicks={0}
          onNodeClick={handleNodeClick}
          enableNodeDrag={false}
        />
      )}
    </div>
  );
}
