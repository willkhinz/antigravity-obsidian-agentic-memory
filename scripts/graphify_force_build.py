#!/usr/bin/env python3
"""
graphify_force_build.py — Headless Graphify AST Knowledge Graph Builder

Builds graph.json and GRAPH_REPORT.md for configured workspace repositories,
then exports nodes, communities, cohesion scores, and links directly to the
Obsidian vault (~/ObsidianVault/graphify-brain).

Covers 20+ programming languages using AST extraction (tree-sitter based).
"""

import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Graphify module imports
try:
    from graphify.detect import detect
    from graphify.extract import collect_files, extract
    from graphify.build import build
    from graphify.cluster import cluster, cohesion_score
    from graphify.report import generate
    from graphify.export import to_obsidian
    import networkx as nx
except ImportError:
    print("[WARNING] 'graphify' package not found in current Python environment.")
    print("Please install graphify via pip / uv before running force build.")

VAULT = Path.home() / "ObsidianVault" / "graphify-brain"
LOG = Path.home() / "graphify_force_build.log"

WORKSPACES = [
    (Path("~/OpenclawSwarm").expanduser(), "openclaw-swarm"),
    (Path("~/Documents/antigravity-skills/LearnHaus AI").expanduser(), "learnhaus-ai"),
    (Path("~/Documents/Jarvis").expanduser(), "jarvis"),
    (Path("~/Documents/Polymarket").expanduser(), "polymarket"),
    (Path("~/Documents/hinzwilliam52-ship-it").expanduser(), "ship-it"),
    (Path("~/Documents/uncanny-road").expanduser(), "uncanny-road"),
    (Path("~/Documents/Upgrades").expanduser(), "upgrades"),
    (Path("~/Documents/Chromebook").expanduser(), "chromebook"),
    (Path("~/Documents/OpenAI competition").expanduser(), "openai-competition"),
    (Path("~/PycharmProjects/PythonProject").expanduser(), "python-project"),
    (Path("~/PycharmProjects/application.dev").expanduser(), "application-dev"),
    (Path("~/ai_completion").expanduser(), "ai-completion"),
    (Path("~/guacamole").expanduser(), "guacamole"),
]


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def build_project(project_path: Path, project_name: str) -> bool:
    out_dir = project_path / "graphify-out"
    out_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(project_path)

    try:
        log("    collecting source files...")
        files = collect_files(project_path)
        if not files:
            log("    ⚠ no code files found — skipping")
            return False
        log(f"    found {len(files)} files")

        log("    running AST extraction...")
        extraction = extract(files)
        nodes = len(extraction.get("nodes", []))
        edges = len(extraction.get("edges", []))
        log(f"    extracted {nodes} nodes, {edges} edges")

        if nodes == 0:
            log("    ⚠ empty extraction — skipping")
            return False

        (out_dir / ".graphify_extract.json").write_text(json.dumps(extraction))

        G = build([extraction])
        log(f"    graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        communities = cluster(G)
        raw_cohesion = cohesion_score(G, communities)
        if isinstance(raw_cohesion, dict):
            cohesion = raw_cohesion
        else:
            cohesion = {k: float(raw_cohesion) for k in communities}
        labels = {k: f"Community {k}" for k in communities}
        log(f"    {len(communities)} communities detected")

        graph_data = nx.node_link_data(G)
        payload = {
            "graph": graph_data,
            "communities": {str(k): list(v) for k, v in communities.items()},
            "community_labels": labels,
            "cohesion": cohesion,
            "built_at": datetime.now().isoformat(),
            "project": project_name,
            "mode": "ast-only",
        }
        (out_dir / "graph.json").write_text(json.dumps(payload, indent=2))

        degree_sorted = sorted(G.degree(), key=lambda x: x[1], reverse=True)
        god_nodes = [
            {"id": n, "degree": d, "label": G.nodes[n].get("label", n)}
            for n, d in degree_sorted[:20]
        ]
        total_words = sum(
            len(G.nodes[n].get("docstring", "").split()) for n in G.nodes
        )
        detect_result = {
            "total_files": len(files),
            "total_words": total_words,
            "code": len(files),
            "doc": 0,
            "image": 0,
            "video": 0,
        }
        token_cost = {"input": 0, "output": 0}

        try:
            report_md = generate(
                G,
                communities,
                cohesion,
                labels,
                god_nodes,
                [],
                detect_result,
                token_cost,
                str(project_path),
            )
        except Exception as rep_err:
            report_md = f"# {project_name} — Knowledge Graph\n\n"
            report_md += f"- **Nodes**: {G.number_of_nodes()}\n"
            report_md += f"- **Edges**: {G.number_of_edges()}\n"
            report_md += f"- **Communities**: {len(communities)}\n\n"
            report_md += "## God Nodes (highest degree)\n\n"
            for gn in god_nodes[:10]:
                report_md += f"- `{gn['label']}` (degree {gn['degree']})\n"
            log(f"    ⚠ report.generate fallback: {rep_err}")

        (out_dir / "GRAPH_REPORT.md").write_text(report_md)
        log(f"    GRAPH_REPORT.md written ({len(report_md)} chars)")

        obsidian_dir = VAULT / project_name
        obsidian_dir.mkdir(parents=True, exist_ok=True)
        n = to_obsidian(
            G,
            communities,
            str(obsidian_dir),
            community_labels=labels,
            cohesion=cohesion,
        )
        log(f"    ✅ Obsidian: {n} notes → {obsidian_dir}")
        return True

    except Exception as e:
        log(f"    ❌ error: {e}")
        import traceback

        traceback.print_exc()
        return False


def write_vault_index(exported: list[str]):
    index = VAULT / "README.md"
    lines = [
        "# Graphify Brain — All Projects\n\n",
        f"*Built: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (AST-only pass)*\n\n",
        "> Full semantic graph (LLM pass) runs when you type `/graphify` inside your agent CLI.\n\n",
        "## Projects\n\n",
    ]
    for name in sorted(exported):
        lines.append(f"- [[{name}/index|{name}]]\n")
    index.write_text("".join(lines))


def main():
    VAULT.mkdir(parents=True, exist_ok=True)
    log("════ graphify force-build (AST-only) ════")

    ok_count = 0
    exported = []

    for project_path, project_name in WORKSPACES:
        if not project_path.exists():
            log(f"⏭ {project_name}: not found")
            continue

        log(f"📁 {project_name}")
        t0 = time.time()
        ok = build_project(project_path, project_name)
        elapsed = time.time() - t0

        if ok:
            ok_count += 1
            exported.append(project_name)
            log(f"    done in {elapsed:.1f}s")
        log("")

    write_vault_index(exported)
    log(f"════ Done: {ok_count}/{len(WORKSPACES)} projects built ════")
    log(f"    Vault: {VAULT}")
    log(f"    Log:   {LOG}")


if __name__ == "__main__":
    main()
