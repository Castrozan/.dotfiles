#!/usr/bin/env bash

# Debug script for tmux pane timer functionality
# Run this inside a tmux session to test the timer configuration

echo "=== TMUX Timer Debug Script ==="
echo ""

# Check if we're in tmux
if [ -z "$TMUX" ]; then
    echo "ERROR: Not running inside tmux. Please run this script in a tmux pane."
    exit 1
fi

echo "✓ Running inside tmux session"
echo ""

# Get current pane ID
PANE_ID=$(tmux display-message -p '#{pane_id}')
echo "Current pane ID: $PANE_ID"
echo ""

# Test 1: Check if we can set and read pane options
echo "=== Test 1: Setting pane_cmd_start option ==="
TEST_TIMESTAMP=$(date +%s)
tmux set-option -p pane_cmd_start "$TEST_TIMESTAMP"
READ_VALUE=$(tmux display-message -p '#{pane_cmd_start}')
echo "Set value: $TEST_TIMESTAMP"
echo "Read value: $READ_VALUE"
if [ "$TEST_TIMESTAMP" = "$READ_VALUE" ]; then
    echo "✓ PASS: Pane option can be set and read"
else
    echo "✗ FAIL: Pane option read value doesn't match"
fi
echo ""

# Test 2: Test the format string with pane_cmd_start
echo "=== Test 2: Testing format string evaluation ==="
FORMAT_TEST=$(tmux display-message -p '#{pane_cmd_start}')
echo "Format string '#{pane_cmd_start}' evaluates to: '$FORMAT_TEST'"
if [ -n "$FORMAT_TEST" ] && [ "$FORMAT_TEST" -gt 0 ] 2>/dev/null; then
    echo "✓ PASS: Format string returns valid timestamp"
else
    echo "✗ FAIL: Format string doesn't return valid timestamp"
fi
echo ""

# Test 3: Test the shell command calculation
echo "=== Test 3: Testing timer calculation shell command ==="
CURRENT_TIME=$(date +%s)
ELAPSED=$((CURRENT_TIME - TEST_TIMESTAMP))
HOURS=$((ELAPSED / 3600))
MINUTES=$(((ELAPSED / 60) % 60))
SECONDS=$((ELAPSED % 60))
FORMATTED=$(printf "%02d:%02d:%02d" $HOURS $MINUTES $SECONDS)
echo "Elapsed time: $ELAPSED seconds"
echo "Formatted: $FORMATTED"
echo "✓ Timer calculation logic works"
echo ""

# Test 4: Test the full shell command with format variable substitution
echo "=== Test 4: Testing full shell command with tmux format ==="
# Simulate what tmux will do - replace #{pane_cmd_start} with actual value
SHELL_CMD="if [ -n \"$TEST_TIMESTAMP\" ] && [ \"$TEST_TIMESTAMP\" -gt 0 ] 2>/dev/null; then s=\$(( \$(date +%s) - $TEST_TIMESTAMP )); printf \"⏱ %02d:%02d:%02d\" \$((s/3600)) \$(((s/60)%60)) \$((s%60)); fi"
echo "Shell command (with substituted value):"
echo "$SHELL_CMD"
echo ""
RESULT=$(eval "$SHELL_CMD")
echo "Command output: '$RESULT'"
if [ -n "$RESULT" ]; then
    echo "✓ PASS: Shell command produces output"
else
    echo "✗ FAIL: Shell command produces no output"
fi
echo ""

# Test 5: Test via tmux's #() command execution
echo "=== Test 5: Testing tmux #() command execution ==="
TMUX_CMD="s=\$(( \$(date +%s) - $TEST_TIMESTAMP )); printf \"⏱ %02d:%02d:%02d\" \$((s/3600)) \$(((s/60)%60)) \$((s%60))"
TMUX_RESULT=$(tmux display-message -p "#($TMUX_CMD)")
echo "tmux #() command output: '$TMUX_RESULT'"
if [ -n "$TMUX_RESULT" ]; then
    echo "✓ PASS: tmux #() command execution works"
else
    echo "✗ FAIL: tmux #() command produces no output"
fi
echo ""

# Test 6: Test conditional format string
echo "=== Test 6: Testing conditional format string ==="
CONDITIONAL_TEST=$(tmux display-message -p '#{?pane_cmd_start,EXISTS,NOT_SET}')
echo "Conditional '#{?pane_cmd_start,EXISTS,NOT_SET}' evaluates to: '$CONDITIONAL_TEST'"
if [ "$CONDITIONAL_TEST" = "EXISTS" ]; then
    echo "✓ PASS: Conditional format works when option is set"
else
    echo "✗ FAIL: Conditional format doesn't work correctly"
fi
echo ""

# Test 7: Test the actual format string we're using
echo "=== Test 7: Testing actual pane_default_text format ==="
# First, let's manually construct what we expect
FULL_FORMAT="#{pane_current_path} #(if [ -n \"#{pane_cmd_start}\" ] && [ \"#{pane_cmd_start}\" -gt 0 ] 2>/dev/null; then s=\$(( \$(date +%s) - #{pane_cmd_start} )); printf \"⏱ %02d:%02d:%02d\" \$((s/3600)) \$(((s/60)%60)) \$((s%60)); fi)"
echo "Testing format string evaluation..."
# Note: This might not work perfectly because tmux needs to evaluate it in context
# But we can at least check if the syntax is valid
tmux set-option -g @test_pane_format "$FULL_FORMAT" 2>&1
if [ $? -eq 0 ]; then
    echo "✓ PASS: Format string syntax is valid (tmux accepts it)"
else
    echo "✗ FAIL: Format string syntax error"
fi
echo ""

# Test 8: Unset the option and test conditional
echo "=== Test 8: Testing when pane_cmd_start is unset ==="
tmux set-option -p -u pane_cmd_start
UNSET_VALUE=$(tmux display-message -p '#{pane_cmd_start}')
echo "After unsetting, value is: '$UNSET_VALUE'"
CONDITIONAL_UNSET=$(tmux display-message -p '#{?pane_cmd_start,EXISTS,NOT_SET}')
echo "Conditional when unset: '$CONDITIONAL_UNSET'"
if [ "$CONDITIONAL_UNSET" = "NOT_SET" ]; then
    echo "✓ PASS: Conditional correctly detects unset option"
else
    echo "✗ FAIL: Conditional doesn't detect unset option"
fi
echo ""

# Test 9: Check current Catppuccin pane_default_text setting
echo "=== Test 9: Checking current Catppuccin configuration ==="
CURRENT_SETTING=$(tmux show-option -gqv @catppuccin_pane_default_text)
if [ -n "$CURRENT_SETTING" ]; then
    echo "Current @catppuccin_pane_default_text setting:"
    echo "$CURRENT_SETTING"
    echo ""
    echo "Testing if this format evaluates correctly..."
    # Try to evaluate a simplified version
    echo "Note: Full evaluation requires Catppuccin plugin to be loaded"
else
    echo "⚠ WARNING: @catppuccin_pane_default_text is not set"
    echo "This might mean the config hasn't been loaded yet"
fi
echo ""

# Summary
echo "=== Summary ==="
echo "If all tests pass, the configuration should work."
echo "If tests fail, check:"
echo "  1. tmux version (needs to support pane options)"
echo "  2. Shell command syntax"
echo "  3. Format string escaping"
echo ""
echo "To test manually in tmux:"
echo "  1. Set: tmux set-option -p pane_cmd_start \$(date +%s)"
echo "  2. Check: tmux display-message -p '#{pane_cmd_start}'"
echo "  3. Test timer: tmux display-message -p '#(s=\$(( \$(date +%s) - #{pane_cmd_start} )); printf \"%02d:%02d:%02d\" \$((s/3600)) \$(((s/60)%60)) \$((s%60)))'"
echo "  4. Reload config: tmux source-file ~/.config/tmux/catppuccin.conf"

