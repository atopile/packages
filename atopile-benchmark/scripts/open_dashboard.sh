#!/bin/bash
# Open the dashboard in your default browser

PORT=8080
URL="http://127.0.0.1:${PORT}"

echo "Opening dashboard at ${URL}..."

# Check if dashboard is running
if curl -s "${URL}/api/config" > /dev/null 2>&1; then
    echo "✓ Dashboard is running"

    # Open in browser
    if command -v open &> /dev/null; then
        # macOS
        open "${URL}"
    elif command -v xdg-open &> /dev/null; then
        # Linux
        xdg-open "${URL}"
    elif command -v start &> /dev/null; then
        # Windows
        start "${URL}"
    else
        echo "Please open ${URL} in your browser"
    fi
else
    echo "✗ Dashboard is not running!"
    echo "Start it with: uv run python main.py"
    exit 1
fi
