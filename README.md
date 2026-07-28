# Antigravity Obsidian Agentic Memory System

> **A complete multi-agent persistent memory ecosystem integrating Graphify knowledge graphs, Obsidian Vault bidirectional note-syncing, 3D WebGL graph visualizers, Shared-Memory MCP servers, and AST Token Context Compilers.**

---

## 🌌 Overview

The **Antigravity Obsidian Agentic Memory System** enables autonomous AI coding agents to maintain persistent, cross-session, multi-project context across local environments.

Instead of scanning thousands of raw source lines on every turn, agents query structured knowledge graphs, navigate community clusters, compile exact AST function code slices, and persist architectural decisions into a Markdown-native Obsidian knowledge base.

```
       ┌────────────────────────────────────────────────────────┐
       │                Agent Execution Session                 │
       └──────────────────────────┬─────────────────────────────┘
                                  │
      ┌───────────────────────────┴───────────────────────────┐
      ▼                                                       ▼
┌──────────────┐                                    ┌──────────────────┐
│  Graphify    │                                    │  Shared-Memory   │
│  AST Pipeline│                                    │    MCP Server    │
└──────┬───────┘                                    └────────┬─────────┘
       │                                                     │
       ▼                                                     ▼
┌──────────────────┐  Sync Daemon  ┌──────────────┐  SQLite & JSON Index
│   graph.json &   ├──────────────►│ Obsidian     │  (~/.mcp-memory)
│ GRAPH_REPORT.md  │               │ Vault        │
└──────┬───────────┘               └──────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│     Antigravity Graph Engine (FastAPI 3333)     │
│   • 3D WebGL Visualizer (React + ThreeJS)      │
│   • Agent Context Compiler (/api/compile/{proj})│
└─────────────────────────────────────────────────┘
```

---

## 📁 Repository Structure

```
antigravity-obsidian-agentic-memory/
├── scripts/
│   ├── graphify_force_build.py      # Multi-language AST graph builder & Obsidian exporter
│   ├── graphify_obsidian_sync.py    # Auto-sync daemon exporting graphs to Obsidian vault
│   └── bootstrap_workspaces.sh      # Bootstraps graphify & .agent/ across all project workspaces
├── graph-engine/                    # 3D WebGL Graph Visualizer & FastAPI Agent Context API
│   ├── server.py                    # FastAPI server on port 3333 (Context Compiler API)
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── App.jsx                  # 3D Force Graph WebGL Canvas
│       ├── App.css
│       ├── main.jsx
│       └── index.css
├── mcp/
│   └── shared_memory_config.json    # MCP Server configuration for persistent agent memory
├── systemd_launchd/
│   └── com.antigravity.obsidian-sync.plist # macOS LaunchDaemon for background vault auto-sync
└── README.md                        # Documentation & setup guide
```

---

## 🚀 Components & Workflow

### 1. Graphify Knowledge Graph Engine
- **AST-based Codebase Graphing**: Parses code across 20+ programming languages without needing LLM calls for initial pass.
- **Leiden Community Detection**: Clusters functions, classes, modules, and dependencies into named architectural communities.
- **God Node Identification**: Detects central hub nodes with high connectivity degree to guide agent navigation.

### 2. Obsidian Vault Integration (`~/ObsidianVault/graphify-brain`)
- **Automated Sync Daemon (`graphify_obsidian_sync.py`)**: Exports `graph.json` structures into linked Obsidian Markdown notes (`[[project/index]]`, community hubs, and node cards).
- **Master Vault Index (`README.md`)**: Automatically updated master table of contents linking all project graphs in Obsidian.

### 3. Antigravity Graph Engine & Agent Context Compiler
- **FastAPI API (`server.py` on port 3333)**:
  - `GET /api/projects`: List all active projects in the Obsidian brain vault.
  - `GET /api/graph/{project}`: Fetch graph data with injected concept hubs (`★ SHARED_CONCEPT`).
  - `GET /api/context/{project}?node=...&depth=2`: Query ego-subgraphs up to $N$ hops away.
  - `GET /api/compile/{project}?node=...`: **Token-Optimized Context Compiler** — reads AST ranges to return only the exact target code block + immediate dependencies, drastically saving context tokens.
- **3D WebGL Interactive Frontend**: Built with React, Vite, Three.js, and Lucide icons for real-time visual inspection of multi-project networks.

### 4. Shared-Memory MCP Server (`mcp-shared-memory`)
- **Cross-Session Persistence**: Stores entities, concepts, decisions, and session notes in `~/.mcp-memory/memory.db`.
- **MCP Tool Suite**: `create_memory`, `search_memories`, `relate_memories`, `rebuild_index`.

---

## 🛠 Setup & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+ & npm
- Obsidian (optional, for viewing vault notes)

### 1. Install Dependencies
```bash
# Python requirements
pip install fastapi uvicorn ujson networkx graphify

# Graph Engine Web App
cd graph-engine
npm install
```

### 2. Run the Graph Engine & Visualizer
```bash
# Terminal 1: Run FastAPI backend
python graph-engine/server.py

# Terminal 2: Run React 3D frontend
cd graph-engine
npm run dev
```

### 3. Sync to Obsidian Vault
```bash
# Run manual sync
python scripts/graphify_obsidian_sync.py

# Or force rebuild all codebase graphs
python scripts/graphify_force_build.py
```

### 4. Enable macOS Background Auto-Sync (Optional)
```bash
cp systemd_launchd/com.antigravity.obsidian-sync.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.antigravity.obsidian-sync.plist
```

---

## 📄 License
MIT License. Built for autonomous AI agents and pair-programming workflows.
