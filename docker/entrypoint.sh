#!/bin/sh
set -e

# Uses tunes' in-memory session registry, so 1 worker keeps it consistent.
cd /app/backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1 &

sleep 2

exec nginx -g 'daemon off;'
