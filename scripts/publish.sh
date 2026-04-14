#!/bin/zsh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 scripts/update_data.py

git add data docs README.md scripts update-now.sh
if ! git diff --cached --quiet; then
  git commit -m "chore: update fund dashboard $(date '+%Y-%m-%d %H:%M:%S')"
  git push origin main
fi
