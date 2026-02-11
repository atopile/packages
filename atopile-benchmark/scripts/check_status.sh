#!/bin/bash
# Quick status checker for the dashboard

echo "📊 atopile Benchmark Dashboard Status"
echo "======================================"
echo ""

# Check if dashboard is running
if curl -s http://127.0.0.1:8080/api/config > /dev/null 2>&1; then
    echo "✅ Dashboard: RUNNING at http://127.0.0.1:8080"
else
    echo "❌ Dashboard: NOT RUNNING"
    echo "   Start with: uv run python main.py"
    exit 1
fi

echo ""
echo "📈 Results Summary:"
echo "-------------------"

# Get results count
RESULTS=$(curl -s http://127.0.0.1:8080/api/results | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)
echo "Total results: $RESULTS"

# Get running count
RUNNING=$(curl -s http://127.0.0.1:8080/api/running | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)
if [ "$RUNNING" -gt 0 ]; then
    echo "🔄 Currently running: $RUNNING benchmarks"
else
    echo "⏸️  No benchmarks currently running"
fi

echo ""
echo "📋 Recent Results:"
echo "------------------"
curl -s http://127.0.0.1:8080/api/results | python3 -c "
import sys, json
results = json.load(sys.stdin)
for r in sorted(results, key=lambda x: x.get('timestamp', ''), reverse=True)[:5]:
    status = '✅' if r['status'] == 'success' else '❌'
    time = f\"{r.get('total_time', 0):.2f}s\" if r.get('total_time') else 'N/A'
    print(f\"{status} {r['benchmark_name']:30} @ {r['version_spec']['version']:10} = {time}\")
" 2>/dev/null

echo ""
echo "🌐 Dashboard: http://127.0.0.1:8080"
echo "🐛 Debug Tool: open debug_data.html"
echo "📝 Full Status: cat FINAL_STATUS.md"
