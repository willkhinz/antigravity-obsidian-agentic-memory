from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import os
import re
import ast
import ujson
from pathlib import Path
from typing import Optional, Dict, List, Any
import networkx as nx

app = FastAPI(
    title="Antigravity Graph Engine API",
    description="Context Compiler API with Token Optimization for AI Coding Agents",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

VAULT_DIR = Path(os.path.expanduser("~/ObsidianVault/graphify-brain"))
PROJECT_CACHE: Dict[str, Path] = {}


def parse_line_number(loc_str: Any) -> Optional[int]:
    """Safely extracts starting line integer from location strings like 'L123', '123', 'L123-L145'."""
    if not loc_str:
        return None
    match = re.search(r'\d+', str(loc_str))
    if match:
        return int(match.group(0))
    return None


def estimate_tokens(text: str) -> int:
    """Estimates token count (~4 characters per token average for code/markdown)."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def strip_comments_and_docstrings(code_str: str) -> str:
    """Strips comments and unnecessary blank lines to maximize LLM token efficiency."""
    lines = code_str.splitlines()
    cleaned = []
    in_multiline_comment = False
    
    for line in lines:
        stripped = line.strip()
        
        # Skip single-line comments
        if stripped.startswith('#') or stripped.startswith('//'):
            continue
            
        # Strip trailing inline comments for non-string occurrences
        if '#' in line and not ('"' in line or "'" in line):
            line = line.split('#')[0].rstrip()
        elif '//' in line and not ('"' in line or "'" in line or 'http' in line):
            line = line.split('//')[0].rstrip()
            
        if not line.strip():
            continue
            
        cleaned.append(line)
        
    return "\n".join(cleaned)


def find_project_graph(project: str) -> Path:
    """Dynamically resolves project graph.json location with caching."""
    if project in PROJECT_CACHE and PROJECT_CACHE[project].exists():
        return PROJECT_CACHE[project]
        
    standard_bases = [
        "~/Documents",
        "~/PycharmProjects",
        "~/ai_completion",
        "~/guacamole",
        "~/Documents/antigravity-skills",
        "~/ObsidianVault/graphify-brain",
        "~/.gemini/antigravity/scratch",
        "~"
    ]
    
    for base in standard_bases:
        base_path = Path(os.path.expanduser(base))
        if not base_path.exists():
            continue

        target = base_path / project / "graphify-out" / "graph.json"

        # Check common project directory aliases
        aliases = [
            ("learnhaus-ai", "LearnHaus AI"),
            ("openai-competition", "OpenAI competition"),
            ("application-dev", "application.dev"),
            ("ship-it", "hinzwilliam52-ship-it"),
            ("python-project", "PythonProject")
        ]
        for alias_key, alias_dir in aliases:
            if project.lower() == alias_key and (base_path / alias_dir / "graphify-out" / "graph.json").exists():
                target = base_path / alias_dir / "graphify-out" / "graph.json"
                break

        if target.exists():
            PROJECT_CACHE[project] = target
            return target

        # Depth=1 search
        try:
            for d in base_path.iterdir():
                if d.is_dir() and project.lower() in d.name.lower():
                    alt_target = d / "graphify-out" / "graph.json"
                    if alt_target.exists():
                        PROJECT_CACHE[project] = alt_target
                        return alt_target
        except PermissionError:
            continue

    raise HTTPException(status_code=404, detail=f"graph.json not found for project '{project}'")


@app.get("/api/projects")
def list_projects():
    projects = set()
    if VAULT_DIR.exists():
        for d in VAULT_DIR.iterdir():
            if d.is_dir() and not d.name.startswith("."):
                projects.add(d.name)
                
    # Also check local scratch / workspace projects
    scratch_dir = Path(os.path.expanduser("~/.gemini/antigravity/scratch"))
    if scratch_dir.exists():
        for d in scratch_dir.iterdir():
            if d.is_dir() and (d / "graphify-out" / "graph.json").exists():
                projects.add(d.name)

    return {"projects": sorted(list(projects))}


@app.get("/api/graph/{project}")
def get_graph(project: str):
    graph_path = find_project_graph(project)

    with open(graph_path, "r", encoding="utf-8") as f:
        graph_data = ujson.load(f)

    return inject_internal_concept_links(graph_data)


def inject_internal_concept_links(graph_data: Dict[str, Any]) -> Dict[str, Any]:
    """Injects structural hubs for nodes sharing key conceptual labels."""
    graph = graph_data.get("graph", {})
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", []) or graph.get("links", [])
    communities = graph_data.get("communities", {})
    communities["SHARED_CONCEPT"] = "SHARED_CONCEPT"

    label_to_nodes: Dict[str, List[Dict]] = {}

    for node in nodes:
        label = str(node.get("label", ""))
        if label and len(label) > 2 and label.lower() not in ["main", "index", "init.py", "__init__.py"]:
            label_to_nodes.setdefault(label, []).append(node)

    concept_id_counter = 0
    for label, matching_nodes in label_to_nodes.items():
        if len(matching_nodes) > 1:
            concept_id = f"LOCAL_CONCEPT_{concept_id_counter}"
            concept_id_counter += 1

            nodes.append({
                "id": concept_id,
                "label": f"★ {label}",
                "community": "SHARED_CONCEPT",
                "file_type": "concept",
                "val": len(matching_nodes) * 2,
            })

            for n in matching_nodes:
                edges.append({
                    "source": n["id"],
                    "target": concept_id,
                    "relation": "implements_concept",
                    "weight": 2.0,
                })

    return {"graph": {"nodes": nodes, "edges": edges}, "communities": communities}


@app.get("/api/context/{project}")
def get_node_context(
    project: str, 
    node: str, 
    depth: int = Query(default=2, ge=1, le=5),
    compact: bool = Query(default=True, description="Compact output format for token saving")
):
    """Query ego-subgraph neighborhood around target node."""
    data = get_graph(project)
    G = nx.node_link_graph(data["graph"])

    if node not in G:
        matches = [n for n in G.nodes if node.lower() in str(n).lower()]
        if not matches:
            raise HTTPException(status_code=404, detail=f"Node '{node}' not found in graph")
        node = matches[0]

    subG = nx.ego_graph(G, node, radius=depth)

    if compact:
        # Ultra-compact list of node labels and relationships for minimal token consumption
        compact_nodes = [
            {"id": n, "label": G.nodes[n].get("label", n), "type": G.nodes[n].get("file_type", "node")}
            for n in subG.nodes
        ]
        compact_edges = [
            {"u": u, "v": v, "rel": edata.get("relation", "connects")}
            for u, v, edata in subG.edges(data=True)
        ]
        return {
            "core_node": node,
            "total_nodes": len(compact_nodes),
            "total_edges": len(compact_edges),
            "nodes": compact_nodes,
            "edges": compact_edges,
            "estimated_tokens": estimate_tokens(ujson.dumps(compact_nodes) + ujson.dumps(compact_edges))
        }

    return {
        "core_node": node,
        "nodes": list(subG.nodes(data=True)),
        "edges": list(subG.edges(data=True)),
        "estimated_tokens": estimate_tokens(ujson.dumps(list(subG.nodes(data=True))))
    }


@app.get("/api/compile/{project}")
def compile_context(
    project: str, 
    node: str,
    compress: bool = Query(default=True, description="Strip comments and redundant whitespace for token compression"),
    max_tokens: int = Query(default=2000, ge=100, le=10000, description="Max token budget limit"),
    include_deps: bool = Query(default=True, description="Include code slices for immediate AST dependencies")
):
    """
    AST Context Compiler: Slices physical code and immediate AST dependencies.
    Optimizes LLM prompt token usage by up to 60%.
    """
    data = get_graph(project)
    G = nx.node_link_graph(data["graph"])

    target = None
    for n, attrs in G.nodes(data=True):
        label = attrs.get("label", "")
        if label and (label.lower() == node.lower() or node.lower() in label.lower()):
            target = dict(attrs)
            target["id"] = n
            break

    if not target:
        raise HTTPException(status_code=404, detail=f"Target node '{node}' not found.")

    src_file = target.get("source_file")
    src_loc = target.get("source_location", "")
    start_line = parse_line_number(src_loc)

    if not src_file or not os.path.exists(src_file) or start_line is None:
        return {
            "markdown_context": f"⚠️ Cannot slice physical code for `{target.get('label', node)}`. Source file missing or unmapped.",
            "raw_tokens": 0,
            "compressed_tokens": 0,
            "tokens_saved": 0
        }

    # Find end line by checking next node in file
    siblings = []
    for n, attrs in G.nodes(data=True):
        if attrs.get("source_file") == src_file:
            s_line = parse_line_number(attrs.get("source_location"))
            if s_line is not None:
                siblings.append(s_line)

    siblings = sorted(list(set(siblings)))
    end_line = None
    for idx in siblings:
        if idx > start_line:
            end_line = idx
            break

    with open(src_file, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    if not end_line:
        end_line = len(lines) + 1

    raw_code = "".join(lines[start_line - 1 : end_line - 1])
    code_to_render = strip_comments_and_docstrings(raw_code) if compress else raw_code

    # Calculate dependencies
    deps_markdown = ""
    seen_dep_files = set()

    if include_deps:
        for u, v, edata in G.edges(target["id"], data=True):
            dep_node = G.nodes[v]
            d_label = dep_node.get("label", str(v))
            d_src_file = dep_node.get("source_file")
            d_start_line = parse_line_number(dep_node.get("source_location"))

            if d_src_file and os.path.exists(d_src_file) and d_start_line is not None:
                dep_key = f"{d_src_file}:{d_start_line}"
                if dep_key in seen_dep_files:
                    continue
                seen_dep_files.add(dep_key)

                d_siblings = [
                    parse_line_number(n_attrs.get("source_location"))
                    for n_id, n_attrs in G.nodes(data=True)
                    if n_attrs.get("source_file") == d_src_file
                ]
                valid_d_siblings = [s for s in d_siblings if s is not None and s > d_start_line]
                d_end_line = sorted(valid_d_siblings)[0] if valid_d_siblings else None

                with open(d_src_file, "r", encoding="utf-8", errors="replace") as df:
                    d_lines = df.readlines()
                    d_end_line = d_end_line or (len(d_lines) + 1)

                d_raw_code = "".join(d_lines[d_start_line - 1 : d_end_line - 1])
                d_code = strip_comments_and_docstrings(d_raw_code) if compress else d_raw_code

                deps_markdown += f"#### Dependency: `{d_label}` ({Path(d_src_file).name}: L{d_start_line}-L{d_end_line-1})\n```python\n{d_code.strip()}\n```\n\n"

    # Assemble Markdown Output
    markdown = f"### Token-Optimized AST Context: `{target.get('label')}`\n"
    markdown += f"**File:** `{src_file}` (Lines {start_line}-{end_line-1})\n\n"
    markdown += f"```python\n{code_to_render.strip()}\n```\n\n"
    
    if deps_markdown:
        markdown += f"---\n### AST Dependencies ({len(seen_dep_files)})\n{deps_markdown}"

    raw_tokens = estimate_tokens(raw_code + deps_markdown)
    compressed_tokens = estimate_tokens(markdown)

    # Apply token budget cap if required
    if compressed_tokens > max_tokens:
        char_limit = max_tokens * 4
        markdown = markdown[:char_limit] + "\n\n... [Truncated to fit max_tokens budget]"
        compressed_tokens = estimate_tokens(markdown)

    tokens_saved = max(0, raw_tokens - compressed_tokens)
    savings_percent = round((tokens_saved / raw_tokens * 100), 1) if raw_tokens > 0 else 0.0

    return {
        "markdown_context": markdown,
        "node_metadata": target,
        "metrics": {
            "raw_estimated_tokens": raw_tokens,
            "compressed_tokens": compressed_tokens,
            "tokens_saved": tokens_saved,
            "compression_savings_percent": f"{savings_percent}%",
            "token_budget_cap": max_tokens
        }
    }


@app.get("/api/compact_tree/{project}")
def compact_tree(project: str):
    """Renders high-density Markdown ASCII project structure optimized for system prompts."""
    data = get_graph(project)
    graph = data.get("graph", {})
    nodes = graph.get("nodes", [])
    communities = data.get("communities", {})

    lines = [f"# Compact Knowledge Architecture: `{project}`\n"]
    
    for comm_id, member_ids in communities.items():
        if comm_id == "SHARED_CONCEPT":
            continue
        lines.append(f"## Community: {comm_id}")
        for nid in member_ids[:15]:  # Top 15 nodes per community
            node_match = next((n for n in nodes if n["id"] == nid), None)
            if node_match:
                label = node_match.get("label", nid)
                ftype = node_match.get("file_type", "symbol")
                lines.append(f"  ├── [{ftype}] {label}")
        if len(member_ids) > 15:
            lines.append(f"  └── ... (+{len(member_ids) - 15} more nodes)")
        lines.append("")

    full_text = "\n".join(lines)
    return {
        "ascii_tree_markdown": full_text,
        "estimated_tokens": estimate_tokens(full_text)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3333)
