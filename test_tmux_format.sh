#!/usr/bin/env bash

# Quick test script for tmux format string
# Run this inside a tmux session

if [ -z "$TMUX" ]; then
    echo "ERROR: Not in tmux. Run this in a tmux pane."
    exit 1
fi

echo "Testing tmux format strings..."
echo ""

# Set a test timestamp
TEST_TS=$(date +%s)
tmux set-option -p pane_cmd_start "$TEST_TS"
echo "Set pane_cmd_start to: $TEST_TS"
echo ""

# Test 1: Simple format variable
echo "Test 1: Simple variable"
RESULT1=$(tmux display-message -p '#{pane_cmd_start}')
echo "Result: $RESULT1"
echo ""

# Test 2: Conditional format
echo "Test 2: Conditional format"
RESULT2=$(tmux display-message -p '#{?pane_cmd_start,EXISTS,NOT_SET}')
echo "Result: $RESULT2"
echo ""

# Test 3: Shell command with format variable
echo "Test 3: Shell command with format variable"
RESULT3=$(tmux display-message -p '#(echo "#{pane_cmd_start}")')
echo "Result: $RESULT3"
echo ""

# Test 4: Timer calculation (simplified)
echo "Test 4: Timer calculation"
RESULT4=$(tmux display-message -p '#(s=$(( $(date +%s) - #{pane_cmd_start} )); printf "%02d:%02d:%02d" $((s/3600)) $(((s/60)%60)) $((s%60)))')
echo "Result: $RESULT4"
echo ""

# Test 5: Conditional with timer
echo "Test 5: Conditional with timer"
RESULT5=$(tmux display-message -p '#{?pane_cmd_start,#(s=$(( $(date +%s) - #{pane_cmd_start} )); printf "⏱ %02d:%02d:%02d" $((s/3600)) $(((s/60)%60)) $((s%60))),}')
echo "Result: $RESULT5"
echo ""

# Test 6: Our actual format (with if statement in shell)
echo "Test 6: Our format with if statement"
RESULT6=$(tmux display-message -p '#(if [ -n "#{pane_cmd_start}" ] && [ "#{pane_cmd_start}" -gt 0 ] 2>/dev/null; then s=$(( $(date +%s) - #{pane_cmd_start} )); printf "⏱ %02d:%02d:%02d" $((s/3600)) $(((s/60)%60)) $((s%60)); fi)')
echo "Result: $RESULT6"
echo ""

# Test 7: Test when unset
echo "Test 7: When unset"
tmux set-option -p -u pane_cmd_start
RESULT7=$(tmux display-message -p '#(if [ -n "#{pane_cmd_start}" ] && [ "#{pane_cmd_start}" -gt 0 ] 2>/dev/null; then s=$(( $(date +%s) - #{pane_cmd_start} )); printf "⏱ %02d:%02d:%02d" $((s/3600)) $(((s/60)%60)) $((s%60)); fi)')
echo "Result (should be empty): '$RESULT7'"
echo ""

echo "Done!"

