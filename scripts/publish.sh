#!/bin/zsh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PYTHON="$ROOT/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON="python3"
fi

if "$PYTHON" scripts/update_data.py; then
  git add data docs README.md scripts update-now.sh
  if ! git diff --cached --quiet; then
    git commit -m "chore: update fund dashboard $(date '+%Y-%m-%d %H:%M:%S')"
    git push origin main
  fi
  "$PYTHON" scripts/notify_feishu.py success >> "$ROOT/update.log" 2>&1
else
  ERR_MSG=$(tail -n 50 "$ROOT/update.log" 2>/dev/null || echo 'update_data.py failed')
  "$PYTHON" scripts/notify_feishu.py failure "$ERR_MSG" >> "$ROOT/update.log" 2>&1 || true
  exit 1
fi
