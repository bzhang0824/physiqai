#!/bin/bash
# PhysiqAI Demo Launcher
# Usage: ./launch-demo.sh

echo "🎬 Launching PhysiqAI Demo Showcase..."
echo ""

DEMO_FILE="demo-showcase.html"
DEMO_PATH="$(cd "$(dirname "$0")" && pwd)/$DEMO_FILE"

if [ ! -f "$DEMO_PATH" ]; then
    echo "❌ Error: demo-showcase.html not found"
    exit 1
fi

# Detect OS and open accordingly
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "🍎 Opening on macOS..."
    open "$DEMO_PATH"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "🐧 Opening on Linux..."
    if command -v xdg-open &> /dev/null; then
        xdg-open "$DEMO_PATH"
    elif command -v google-chrome &> /dev/null; then
        google-chrome "$DEMO_PATH"
    elif command -v firefox &> /dev/null; then
        firefox "$DEMO_PATH"
    else
        echo "⚠️  Could not detect browser. Please open manually:"
        echo "   $DEMO_PATH"
    fi
else
    # Windows or other
    echo "🪟 Attempting to open..."
    start "$DEMO_PATH" 2>/dev/null || \
    xdg-open "$DEMO_PATH" 2>/dev/null || \
    echo "⚠️  Please open manually: $DEMO_PATH"
fi

echo ""
echo "✅ Demo launched!"
echo ""
echo "📋 Quick Guide:"
echo "   1. Click the scenario tabs at the top"
echo "   2. Switch between 3 user cards"
echo "   3. Try the avatar slider in Day 30/90"
echo "   4. Click '🎉 Celebrate' for confetti"
echo ""
