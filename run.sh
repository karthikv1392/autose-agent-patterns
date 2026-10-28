#!/usr/bin/env bash
# Launcher for AutoSE Agent Patterns (self-contained: own venv, own node_modules).
# Usage: ./run.sh [app|site|both]     (no argument: asks which one)
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

APP_PORT=8503
SITE_PORT=5173

setup_app() {
  if [ ! -d .venv ]; then
    echo "Creating virtual environment at .venv ..."
    python3 -m venv .venv
    .venv/bin/pip install -q --upgrade pip
    .venv/bin/pip install -q -r requirements.txt
  fi
  if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "Warning: Ollama does not seem to be running (ollama serve)."
  fi
}

setup_site() {
  if ! command -v npm >/dev/null 2>&1; then
    echo "npm not found. Install Node.js 20+ to run the website."; exit 1
  fi
  if [ ! -d website/node_modules ]; then
    echo "Installing website dependencies ..."
    (cd website && npm ci --no-audit --no-fund)
  fi
}

run_app()  { setup_app;  exec .venv/bin/streamlit run app.py --server.port "$APP_PORT"; }
run_site() { setup_site; cd website; exec npm run dev -- --port "$SITE_PORT" --open; }

run_both() {
  setup_site; setup_app
  (cd website && npm run dev -- --port "$SITE_PORT" --open) &
  trap 'kill 0' EXIT
  .venv/bin/streamlit run app.py --server.port "$APP_PORT"
}

choice="${1:-}"
if [ -z "$choice" ]; then
  echo "What would you like to run?"
  echo "  1) Learning website   (http://localhost:$SITE_PORT)"
  echo "  2) Streamlit demo     (http://localhost:$APP_PORT, needs Ollama)"
  echo "  3) Both"
  read -rp "Enter choice [1-3]: " n
  case "$n" in 1) choice=site ;; 2) choice=app ;; 3) choice=both ;; *) echo "Invalid choice: $n"; exit 1 ;; esac
fi

case "$choice" in
  app)  run_app ;;
  site) run_site ;;
  both) run_both ;;
  *) echo "Usage: ./run.sh [app|site|both]"; exit 1 ;;
esac
