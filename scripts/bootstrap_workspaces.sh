#!/usr/bin/env zsh
# bootstrap_workspaces.sh — Apply graphify + antigravity-architect to all workspaces

export PATH="/usr/local/bin:/Library/Frameworks/Python.framework/Versions/3.13/bin:$PATH"

PYTHON="python3"
AA="antigravity-architect"
LOG="$HOME/bootstrap_workspaces.log"

WORKSPACES=(
  "$HOME/OpenclawSwarm"
  "$HOME/Documents/antigravity-skills/LearnHaus AI"
  "$HOME/Documents/Jarvis"
  "$HOME/Documents/Polymarket"
  "$HOME/Documents/hinzwilliam52-ship-it"
  "$HOME/Documents/uncanny-road"
  "$HOME/Documents/Upgrades"
  "$HOME/Documents/Chromebook"
  "$HOME/Documents/OpenAI competition"
  "$HOME/PycharmProjects/PythonProject"
  "$HOME/PycharmProjects/application.dev"
  "$HOME/ai_completion"
  "$HOME/guacamole"
)

echo "" | tee -a "$LOG"
echo "════════════════════════════════════════════════" | tee -a "$LOG"
echo "  Workspace Bootstrap — $(date)" | tee -a "$LOG"
echo "════════════════════════════════════════════════" | tee -a "$LOG"

for WS in "${WORKSPACES[@]}"; do
  if [ ! -d "$WS" ]; then
    echo "⏭  SKIPPED (not found): $WS" | tee -a "$LOG"
    continue
  fi

  echo "" | tee -a "$LOG"
  echo "──────────────────────────────────────────────" | tee -a "$LOG"
  echo "📁  $WS" | tee -a "$LOG"
  echo "──────────────────────────────────────────────" | tee -a "$LOG"

  cd "$WS" || continue

  # ── graphify — build graph via Python module ───────────────────────────────
  echo "🕸  graphify: building knowledge graph..." | tee -a "$LOG"
  if [ -f "graphify-out/graph.json" ]; then
    $PYTHON -c "
from graphify.watch import _rebuild_code
from pathlib import Path
_rebuild_code(Path('.'))
print('  graph updated (incremental)')
" 2>&1 | tee -a "$LOG"
  else
    $PYTHON -m graphify.build_graph . 2>&1 | tail -4 | tee -a "$LOG" || \
    echo "  ⚠  graphify build requires Gemini CLI — GEMINI.md hook is active" | tee -a "$LOG"
  fi

  # Install gemini hook per-project
  graphify gemini install 2>&1 | grep -v "^$" | tee -a "$LOG"

  # ── antigravity-architect ─────────────────────────────────────────────────
  if [ -f ".agent/manifest.json" ]; then
    echo "✅  .agent/ already exists — running --doctor..." | tee -a "$LOG"
    $AA --doctor . 2>&1 | tail -4 | tee -a "$LOG"
  else
    PROJ=$(basename "$WS" | tr ' ' '-' | tr '[:upper:]' '[:lower:]')
    echo "🏗  Scaffolding .agent/ for: $PROJ" | tee -a "$LOG"
    $AA --name "$PROJ" --stack python --safe 2>&1 | tail -6 | tee -a "$LOG"
  fi

done

echo "" | tee -a "$LOG"
echo "════════════════════════════════════════════════" | tee -a "$LOG"
echo "  Done. Full log: $LOG" | tee -a "$LOG"
echo "════════════════════════════════════════════════" | tee -a "$LOG"
