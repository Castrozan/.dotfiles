#!/usr/bin/env bash
# Usage tracker — shows Claude Code subscription usage stats
# Run: bash ~/@workspacePath@/scripts/usage-tracker.sh

CCOST=~/.local/bin/ccost

echo "═══════════════════════════════════════════"
echo "  Claude Usage Dashboard ($(date '+%Y-%m-%d %H:%M BRT'))"
echo "═══════════════════════════════════════════"
echo ""

echo "▸ TODAY"
$CCOST today 2>/dev/null | tail -3
echo ""

echo "▸ THIS WEEK"
$CCOST this-week 2>/dev/null | tail -3
echo ""

echo "▸ ALL TIME"
$CCOST 2>/dev/null | tail -3
echo ""

echo "▸ DAILY BREAKDOWN (last 7 days)"
$CCOST daily --days 7 2>/dev/null
echo ""

echo "▸ CLAUDE CODE STATS"
python3 -c "
import json
with open('$HOME/.claude/stats-cache.json') as f:
    data = json.load(f)
total_msgs = sum(d['messageCount'] for d in data['dailyActivity'])
total_sessions = sum(d['sessionCount'] for d in data['dailyActivity'])
total_tools = sum(d['toolCallCount'] for d in data['dailyActivity'])
last = data['dailyActivity'][-1] if data['dailyActivity'] else {}
print(f'  Total: {total_msgs:,} messages, {total_sessions:,} sessions, {total_tools:,} tool calls')
if last:
    print(f'  Last day ({last[\"date\"]}): {last[\"messageCount\"]:,} msgs, {last[\"sessionCount\"]:,} sessions')
" 2>/dev/null

echo ""
echo "▸ PLAN: Max (\$100/mo) — Usage resets every 5h after cap"
echo "  Tip: Use Opus for complex work, Sonnet for routine tasks"
