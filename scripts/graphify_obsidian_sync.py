#!/usr/bin/env python3
"""
graphify_obsidian_sync.py — Export all workspace graphify graphs to Obsidian vault.
Can be executed manually or via launchd daemon for background auto-sync.
"""

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime

PYTHON = sys.executable
VAULT = Path.home() / "ObsidianVault" / "graphify-brain"
LOG = Path.home() / "graphify_obsidian_sync.log"

WORKSPACES = [
    ("~/OpenclawSwarm", "openclaw-swarm"),
    ("~/Documents/antigravity-skills/LearnHaus AI", "learnhaus-ai"),
    ("~/Documents/Jarvis", "jarvis"),
    ("~/Documents/Polymarket", "polymarket"),
    ("~/Documents/hinzwilliam52-ship-it", "ship-it"),
    ("~/Documents/uncanny-road", "uncanny-road"),
    ("~/Documents/Upgrades", "upgrades"),
    ("~/Documents/Chromebook", "chromebook"),
    ("~/Documents/OpenAI competition", "openai-competition"),
    ("~/PycharmProjects/PythonProject", "python-project"),
    ("~/PycharmProjects/application.dev", "application-dev"),
    ("~/ai_completion", "ai-completion"),
    ("~/guacamole", "guacamole"),
]


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def export_to_obsidian(project_path: Path, project_name: str, vault: Path):
    graph_json = project_path / "graphify-out" / "graph.json"
    obsidian_dir = vault / project_name

    if not graph_json.exists():
        log(f"  ⏭  {project_name}: no graph.json yet — skipping")
        return False

    obsidian_dir.mkdir(parents=True, exist_ok=True)

    code = f"""
import json, sys
sys.path.insert(0, '')
from graphify.export import to_obsidian
from pathlib import Path
import networkx as nx

graph_data = json.loads(Path('{graph_json}').read_text())
G = nx.node_link_graph(graph_data['graph']) if 'graph' in graph_data else nx.Graph()

communities = graph_data.get('communities', {{}})
labels      = graph_data.get('community_labels', None)
cohesion    = graph_data.get('cohesion', {{}})

obsidian_dir = '{obsidian_dir}'
n = to_obsidian(G, communities, obsidian_dir, community_labels=labels, cohesion=cohesion)
print(f'exported {{n}} notes to {{obsidian_dir}}')
"""

    result = subprocess.run(
        [PYTHON, "-c", code],
        cwd=str(project_path),
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        log(f"  ✅  {project_name}: {result.stdout.strip()}")
        return True
    else:
        log(f"  ⚠  {project_name}: {result.stderr.strip()[:200]}")
        return False


def write_vault_index(vault: Path, exported: list[str]):
    """Write a master index note linking all projects in Obsidian."""
    index_path = vault / "README.md"
    lines = [
        "# Graphify Brain — All Projects\n",
        f"*Last synced: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n",
        "## Projects\n",
    ]
    for name in sorted(exported):
        lines.append(f"- [[{name}/index|{name}]]\n")
    index_path.write_text("".join(lines))
    log(f"  📋  Vault index updated ({len(exported)} projects)")


def main():
    log("════ graphify → Obsidian sync started ════")
    VAULT.mkdir(parents=True, exist_ok=True)

    exported = []
    for ws_raw, project_name in WORKSPACES:
        project_path = Path(ws_raw).expanduser()
        if not project_path.exists():
            log(f"  ⏭  {project_name}: path not found")
            continue
        log(f"  📁  {project_name}")
        ok = export_to_obsidian(project_path, project_name, VAULT)
        if ok:
            exported.append(project_name)

    write_vault_index(VAULT, exported)
    log(f"════ Done: {len(exported)}/{len(WORKSPACES)} projects synced ════\n")


if __name__ == "__main__":
    main()
