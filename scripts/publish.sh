#!/bin/zsh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if python3 scripts/update_data.py; then
  git add data docs README.md scripts update-now.sh
  if ! git diff --cached --quiet; then
    git commit -m "chore: update fund dashboard $(date '+%Y-%m-%d %H:%M:%S')"
    git push origin main
  fi
  python3 scripts/notify_feishu.py success >> "$ROOT/update.log" 2>&1 || true
else
  ERR_MSG=$(tail -n 50 "$ROOT/update.log" 2>/dev/null || echo 'update_data.py failed')
  python3 scripts/notify_feishu.py failure "$ERR_MSG" >> "$ROOT/update.log" 2>&1 || true
  exit 1
fi
