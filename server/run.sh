#!/usr/bin/env bash
# Run the PhysiqAI backend locally. Reachable at:
#   iOS Simulator / same machine -> http://localhost:8000
#   physical iPhone (same WiFi)  -> http://<your-mac-LAN-IP>:8000
# FAL_KEY is read from the environment (already in ~/.zshrc).
cd "$(dirname "$0")/.." || exit 1
exec spike/.venv/bin/uvicorn server.app:app --host 0.0.0.0 --port 8000 "$@"
