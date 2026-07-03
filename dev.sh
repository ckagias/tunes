#!/usr/bin/env bash
# Runs both the FastAPI backend and the Vite frontend for local development.
# Ctrl+C stops both.
set -euo pipefail

cd "$(dirname "$0")"

cleanup() {
  echo
  echo "Stopping dev servers…"
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

(
  cd backend
  source .venv/bin/activate
  uvicorn app.main:app --reload --port 8000
) &
BACKEND_PID=$!

(
  cd frontend
  npm run dev
) &
FRONTEND_PID=$!

wait
