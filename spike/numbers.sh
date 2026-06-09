#!/bin/bash
# Instant, free engine numbers. Usage: bash spike/numbers.sh [goal] [weeks] [lean_pref]
# goal: fat_loss|muscle_gain|recomp|maintenance   weeks: 4|12|26|52   pref: standard|lean_bulk|aggressive_bulk
cd /Users/brianzhang/Projects/PhysiqAI || exit 1
spike/.venv/bin/python spike/morph.py --no-image \
  --goal "${1:-fat_loss}" --weeks "${2:-26}" --lean-pref "${3:-standard}"
