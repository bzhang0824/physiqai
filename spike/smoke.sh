#!/usr/bin/env bash
# Live E2E smoke test of the production pipeline on a real photo (~$0.30, 2 gens).
# Usage:  bash spike/smoke.sh [photo_path]
cd "$(dirname "$0")/.." || exit 1
spike/.venv/bin/python spike/smoke_pipeline.py ${1:+--photo "$1"}
