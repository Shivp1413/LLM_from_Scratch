#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
if [[ ! -x .venv/bin/python ]]; then
  echo 'Python environment is not installed. Run: ./Linux_setup/setup.sh'
  exit 1
fi
URL='http://127.0.0.1:7860'
(.venv/bin/python -c 'import time,urllib.request
for _ in range(40):
 try: urllib.request.urlopen("http://127.0.0.1:7860",timeout=.3); break
 except Exception: time.sleep(.25)' && (xdg-open "$URL" >/dev/null 2>&1 || true)) &
exec .venv/bin/python app.py
