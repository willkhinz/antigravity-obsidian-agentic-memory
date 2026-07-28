# Antigravity Obsidian Agentic Memory System

> **A complete multi-agent persistent memory ecosystem integrating Graphify knowledge graphs, Obsidian Vault bidirectional note-syncing, 3D WebGL graph visualizers, Shared-Memory MCP servers, and AST Token Context Compilers.**

---

## 🌌 Overview & Key Features

The **Antigravity Obsidian Agentic Memory System** enables autonomous AI coding agents (Claude Code, Antigravity, Gemini CLI) to maintain persistent, cross-session, multi-project context across local environments.

Instead of scanning thousands of raw source lines on every turn, agents query structured knowledge graphs, navigate community clusters, compile exact AST function code slices, and persist architectural decisions into a Markdown-native Obsidian knowledge base.

### ⚡ Token Optimization Engine (v2.0)
- **Comments & Docstrings Stripper**: Strips non-essential multiline docstrings and comments when fetching AST contexts, saving **30-60% LLM tokens**.
- **AST Code Slicing**: Slices only the exact function/symbol lines and immediate dependencies, rather than reading full 1000-line files.
- **Dependency Deduplication**: Prevents duplicate dependency inclusions when multiple functions import from the same target module.
- **Token Budgeting (`max_tokens`)**: Allows agents to specify bounded token caps (`max_tokens=1500`) to guarantee prompt budget compliance.
- **Compact ASCII Tree Renderer (`/api/compact_tree/{project}`)**: Generates high-density markdown dependency trees for LLM system prompts using **80% fewer tokens** than raw JSON graph payloads.

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
│   • Token Compression & Metrics Dashboard       │
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
│   ├── server.py                    # FastAPI server on port 3333 (Context Compiler API v2)
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── App.jsx                  # 3D Force Graph WebGL Canvas & AST Inspector
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

## 📡 Context Compiler REST Endpoints

### 1. `GET /api/compile/{project}?node=...&compress=true&max_tokens=2000`
Slices the physical code and immediate AST dependencies for a target node with token savings metrics.
```json
{
  "markdown_context": "### Token-Optimized AST Context: `compile_context` ...",
  "metrics": {
    "raw_estimated_tokens": 1240,
    "compressed_tokens": 680,
    "tokens_saved": 560,
    "compression_savings_percent": "45.2%"
  }
}
```

### 2. `GET /api/compact_tree/{project}`
Renders a dense Markdown ASCII tree of communities and top nodes for LLM system prompts.

### 3. `GET /api/context/{project}?node=...&depth=2&compact=true`
Returns ego-subgraph neighborhoods formatted for minimal token overhead.

---

## 🛠 Setup & Installation

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
