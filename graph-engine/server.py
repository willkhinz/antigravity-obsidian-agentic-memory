from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import ujson
from pathlib import Path
import networkx as nx

app = FastAPI(title="Antigravity Graph Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

VAULT_DIR = Path(os.path.expanduser("~/ObsidianVault/graphify-brain"))


@app.get("/api/projects")
def list_projects():
    projects = []
    if VAULT_DIR.exists():
        for d in VAULT_DIR.iterdir():
            if d.is_dir() and not d.name.startswith("."):
                projects.append(d.name)
    return {"projects": sorted(projects)}


@app.get("/api/graph/{project}")
def get_graph(project: str):
    standard_bases = [
        "~/Documents",
        "~/PycharmProjects",
        "~/ai_completion",
        "~/guacamole",
        "~/Documents/antigravity-skills",
        "~/ObsidianVault/graphify-brain",
    ]

    found_path = None
    for base in standard_bases:
        base_path = Path(os.path.expanduser(base))
        if not base_path.exists():
            continue

        target = base_path / project / "graphify-out" / "graph.json"

        if project == "learnhaus-ai" and (
            base_path / "LearnHaus AI" / "graphify-out" / "graph.json"
        ).exists():
            target = base_path / "LearnHaus AI" / "graphify-out" / "graph.json"
        if project == "openai-competition" and (
            base_path / "OpenAI competition" / "graphify-out" / "graph.json"
        ).exists():
            target = base_path / "OpenAI competition" / "graphify-out" / "graph.json"
        if project == "application-dev" and (
            base_path / "application.dev" / "graphify-out" / "graph.json"
        ).exists():
            target = base_path / "application.dev" / "graphify-out" / "graph.json"
        if project == "ship-it" and (
            base_path / "hinzwilliam52-ship-it" / "graphify-out" / "graph.json"
        ).exists():
            target = base_path / "hinzwilliam52-ship-it" / "graphify-out" / "graph.json"
        if project == "python-project" and (
            base_path / "PythonProject" / "graphify-out" / "graph.json"
        ).exists():
            target = base_path / "PythonProject" / "graphify-out" / "graph.json"

        if target.exists():
            found_path = target
            break

        for d in base_path.iterdir():
            if d.is_dir() and project.lower() in d.name.lower():
                alt_target = d / "graphify-out" / "graph.json"
                if alt_target.exists():
                    found_path = alt_target
                    break
        if found_path:
            break

    if not found_path:
        raise HTTPException(
            status_code=404, detail=f"graph.json not found for project '{project}'"
        )

    with open(found_path, "r", encoding="utf-8") as f:
        graph_data = ujson.load(f)

    return inject_internal_concept_links(graph_data)


def inject_internal_concept_links(graph_data):
    """Creates structural hubs within a single project for nodes that share the same concept/label."""
    graph = graph_data.get("graph", {})
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", []) or graph.get("links", [])
    communities = graph_data.get("communities", {})
    communities["SHARED_CONCEPT"] = "SHARED_CONCEPT"

    label_to_nodes = {}

    for node in nodes:
        label = str(node.get("label", ""))
        if (
            label
            and len(label) > 2
            and label.lower() not in ["main", "index", "init.py", "__init__.py"]
        ):
            if label not in label_to_nodes:
                label_to_nodes[label] = []
            label_to_nodes[label].append(node)

    concept_id_counter = 0
    for label, matching_nodes in label_to_nodes.items():
        if len(matching_nodes) > 1:
            concept_id = f"LOCAL_CONCEPT_{concept_id_counter}"
            concept_id_counter += 1

            nodes.append(
                {
                    "id": concept_id,
                    "label": f"★ {label}",
                    "community": "SHARED_CONCEPT",
                    "file_type": "concept",
                    "val": len(matching_nodes) * 2,
                }
            )

            for n in matching_nodes:
                edges.append(
                    {
                        "source": n["id"],
                        "target": concept_id,
                        "relation": "implements_concept",
                        "weight": 2.0,
                    }
                )

    return {"graph": {"nodes": nodes, "edges": edges}, "communities": communities}


@app.get("/api/context/{project}")
def get_node_context(project: str, node: str, depth: int = 2):
    """Query neighbor context up to `depth` edges for agent retrieval."""
    data = get_graph(project)
    G = nx.node_link_graph(data["graph"])

    if node not in G:
        matches = [n for n in G.nodes if node.lower() in str(n).lower()]
        if not matches:
            raise HTTPException(status_code=404, detail="Node not found in graph")
        node = matches[0]

    subG = nx.ego_graph(G, node, radius=depth)

    return {
        "core_node": node,
        "nodes": list(subG.nodes(data=True)),
        "edges": list(subG.edges(data=True)),
    }


@app.get("/api/compile/{project}")
def compile_context(project: str, node: str):
    """Slices physical code & dependencies for a target node (AST Token Compiler)."""
    data = get_graph(project)
    G = nx.node_link_graph(data["graph"])

    target = None
    for n, attrs in G.nodes(data=True):
        label = attrs.get("label", "")
        if label and (label.lower() == node.lower() or node.lower() in label.lower()):
            target = attrs
            target["id"] = n
            break

    if not target:
        raise HTTPException(status_code=404, detail="Target node not found.")

    src_file = target.get("source_file")
    src_loc = target.get("source_location", "")

    if not src_file or not os.path.exists(src_file) or not src_loc.startswith("L"):
        return {
            "context": f"Cannot slice physical code for {target.get('label')}. Missing or invalid file."
        }

    start_line = int(src_loc[1:])

    siblings = []
    for n, attrs in G.nodes(data=True):
        if attrs.get("source_file") == src_file and attrs.get(
            "source_location", ""
        ).startswith("L"):
            try:
                line_idx = int(attrs["source_location"][1:])
                siblings.append(line_idx)
            except Exception:
                pass

    siblings = sorted(list(set(siblings)))

    end_line = None
    for idx in siblings:
        if idx > start_line:
            end_line = idx
            break

    with open(src_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if not end_line:
        end_line = len(lines) + 1

    sliced_code = "".join(lines[start_line - 1 : end_line - 1])

    deps_markdown = ""
    for u, v, edata in G.edges(target["id"], data=True):
        dep_node = G.nodes[v]
        d_src_file = dep_node.get("source_file")
        d_src_loc = dep_node.get("source_location", "")

        if d_src_file and os.path.exists(d_src_file) and d_src_loc.startswith("L"):
            d_start_line = int(d_src_loc[1:])
            d_siblings = [
                int(n_attrs["source_location"][1:])
                for n_id, n_attrs in G.nodes(data=True)
                if n_attrs.get("source_file") == d_src_file
                and n_attrs.get("source_location", "").startswith("L")
                and int(n_attrs["source_location"][1:]) > d_start_line
            ]

            d_end_line = sorted(list(set(d_siblings)))[0] if d_siblings else None

            with open(d_src_file, "r", encoding="utf-8") as df:
                d_lines = df.readlines()
                d_end_line = d_end_line or (len(d_lines) + 1)

            d_sliced_code = "".join(d_lines[d_start_line - 1 : d_end_line - 1])
            deps_markdown += f"#### Relies on: `{dep_node.get('label')}` (Lines {d_start_line}-{d_end_line-1})\n```python\n{d_sliced_code.strip()}\n```\n\n"

    markdown = f"### Token-Optimized Context: `{target.get('label')}`\n"
    markdown += f"**File:** `{src_file}` (Lines {start_line}-{end_line-1})\n\n"
    markdown += f"```python\n{sliced_code.strip()}\n```\n\n"
    if deps_markdown:
        markdown += f"---\n### Dependencies\n{deps_markdown}"

    return {"markdown_context": markdown, "node_metadata": target}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=3333)
