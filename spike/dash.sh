#!/bin/bash
# Rebuild the test dashboard and open it. Usage: bash spike/dash.sh
cd /Users/brianzhang/Projects/PhysiqAI || exit 1
spike/.venv/bin/python spike/dashboard.py && open spike/output/dashboard.html
