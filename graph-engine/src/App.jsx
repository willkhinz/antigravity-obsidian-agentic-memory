import React, { useState, useEffect, useRef, useCallback } from 'react';
import ForceGraph3D from 'react-force-graph-3d';
import axios from 'axios';
import { Layers, Box, Workflow, Loader2 } from 'lucide-react';

const API_BASE = 'http://localhost:3333/api';

export default function App() {
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState('');
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(false);
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
    axios.get(`${API_BASE}/graph/${selectedProject}`).then(res => {
      const g = res.data.graph;
      const parsedData = {
        nodes: g.nodes.map(n => ({
          ...n,
          id: n.id,
          name: n.label || n.id,
          val: (n.degree || 1) * 0.5,
          color: res.data.communities[n.community] ? getColorForCommunity(n.community) : '#1f77b4'
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

  const getColorForCommunity = useCallback((cid) => {
    const colors = ["#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231", "#911eb4", "#46f0f0", "#f032e6", "#bcf60c", "#fabebe", "#008080", "#e6beff", "#9a6324", "#fffac8", "#800000", "#aaffc3", "#808000", "#ffd8b1", "#000075", "#808080", "#ffffff", "#000000"];
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
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, padding: '20px', zIndex: 10, display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'linear-gradient(to bottom, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0) 100%)' }}>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <div style={{ background: 'rgba(255,255,255,0.1)', padding: '10px', borderRadius: '12px', backdropFilter: 'blur(10px)' }}>
            <Layers color="#a855f7" size={24} />
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: '20px', fontWeight: '600', letterSpacing: '-0.5px' }}>Antigravity Graph Engine</h1>
            <p style={{ margin: 0, fontSize: '12px', color: '#9ca3af' }}>WebGL Protocol 3.0.0</p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <select 
            value={selectedProject} 
            onChange={(e) => setSelectedProject(e.target.value)}
            style={{ 
              backgroundColor: 'rgba(255,255,255,0.05)', 
              color: 'white', 
              border: '1px solid rgba(255,255,255,0.1)', 
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
        <div style={{ background: 'rgba(255,255,255,0.05)', padding: '12px 20px', borderRadius: '12px', backdropFilter: 'blur(10px)', border: '1px solid rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Box size={16} color="#4ade80" />
          <span style={{ fontSize: '14px', fontWeight: 500 }}>{graphData.nodes.length.toLocaleString()} Nodes</span>
        </div>
        <div style={{ background: 'rgba(255,255,255,0.05)', padding: '12px 20px', borderRadius: '12px', backdropFilter: 'blur(10px)', border: '1px solid rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Workflow size={16} color="#60a5fa" />
          <span style={{ fontSize: '14px', fontWeight: 500 }}>{graphData.links.length.toLocaleString()} Edges</span>
        </div>
      </div>

      {loading && (
        <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', zIndex: 20, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
          <Loader2 className="lucide-spin" size={48} color="#a855f7" />
          <div style={{ color: '#a855f7', fontWeight: 500 }}>Rendering Canvas...</div>
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
          linkColor={() => 'rgba(255,255,255,0.1)'}
          backgroundColor="#020202"
          showNavInfo={false}
          warmupTicks={100}
          cooldownTicks={0}
          enableNodeDrag={false}
        />
      )}
    </div>
  );
}
