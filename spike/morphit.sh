#!/bin/bash
# Generate the visual morph (~$0.15). Usage: bash spike/morphit.sh [goal] [weeks] [lean_pref] [photo]
cd /Users/brianzhang/Projects/PhysiqAI || exit 1
spike/.venv/bin/python spike/morph.py --photo "${4:-spike/photos/bz02_IMG_7520.png}" \
  --goal "${1:-fat_loss}" --weeks "${2:-26}" --lean-pref "${3:-standard}"
spike/.venv/bin/python spike/dashboard.py >/dev/null 2>&1
