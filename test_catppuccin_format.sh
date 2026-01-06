#!/usr/bin/env bash

# Test script specifically for Catppuccin pane format
# This simulates what Catppuccin plugin does with the format string

if [ -z "$TMUX" ]; then
    echo "ERROR: Not in tmux. Run this in a tmux pane."
    exit 1
fi

echo "=== Testing Catppuccin Pane Format ==="
echo ""

# Set test timestamp
TEST_TS=$(date +%s)
tmux set-option -p pane_cmd_start "$TEST_TS"
echo "Set pane_cmd_start to: $TEST_TS"
echo ""

# Test the exact format we're using
FORMAT_STRING='#{pane_current_path} #{?pane_cmd_start,#(s=$(( $(date +%s) - #{pane_cmd_start} )); printf "⏱ %02d:%02d:%02d" $((s/3600)) $(((s/60)%60)) $((s%60))),}'

echo "Testing format string:"
echo "$FORMAT_STRING"
echo ""

# Test 1: Direct evaluation
echo "Test 1: Direct tmux display-message evaluation"
RESULT1=$(tmux display-message -p "$FORMAT_STRING")
echo "Result: $RESULT1"
echo ""

# Test 2: Set as a test option and see if it works
echo "Test 2: Setting as tmux option"
tmux set-option -g @test_format "$FORMAT_STRING"
if [ $? -eq 0 ]; then
    echo "✓ Format string syntax is valid"
    echo "Value stored: $(tmux show-option -gqv @test_format)"
else
    echo "✗ Format string syntax error"
fi
echo ""

# Test 3: Test conditional separately
echo "Test 3: Testing conditional part only"
COND_PART='#{?pane_cmd_start,EXISTS,NOT_SET}'
COND_RESULT=$(tmux display-message -p "$COND_PART")
echo "Conditional result: $COND_RESULT"
echo ""

# Test 4: Test shell command part only
echo "Test 4: Testing shell command part only"
SHELL_PART='#(s=$(( $(date +%s) - #{pane_cmd_start} )); printf "⏱ %02d:%02d:%02d" $((s/3600)) $(((s/60)%60)) $((s%60)))'
SHELL_RESULT=$(tmux display-message -p "$SHELL_PART")
echo "Shell command result: $SHELL_RESULT"
echo ""

# Test 5: Test when unset
echo "Test 5: Testing when pane_cmd_start is unset"
tmux set-option -p -u pane_cmd_start
UNSET_RESULT=$(tmux display-message -p "$FORMAT_STRING")
echo "Result (should not show timer): $UNSET_RESULT"
echo ""

# Test 6: Check if Catppuccin option is actually set
echo "Test 6: Checking current Catppuccin setting"
CURRENT=$(tmux show-option -gqv @catppuccin_pane_default_text)
if [ -n "$CURRENT" ]; then
    echo "Current @catppuccin_pane_default_text:"
    echo "$CURRENT"
    echo ""
    echo "Evaluating current setting:"
    EVAL_RESULT=$(tmux display-message -p "$CURRENT")
    echo "Result: $EVAL_RESULT"
else
    echo "⚠ @catppuccin_pane_default_text is not set"
fi
echo ""

# Cleanup
tmux set-option -g -u @test_format 2>/dev/null

echo "Done!"

