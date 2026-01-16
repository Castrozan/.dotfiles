---
description: Tmux interaction patterns for AI agents controlling dev servers and processes
alwaysApply: false
---

Do not change this file if not requested or if the change does not follow the pattern that focuses on token usage and information density. Follow these rules when interacting with tmux sessions from AI agents.

Session Discovery
List all windows across sessions with `tmux list-windows -a`. Output format: `session:window: window_name (n panes) [geometry] [flags]`. Use this to understand current tmux state before any interaction.

Pane Discovery
List panes in specific window with `tmux list-panes -t "session:window" -F "#{pane_index}: #{pane_current_command} - #{pane_current_path}"`. The format string shows pane index, running command, and working directory. Essential for identifying which pane runs which process.

Sending Commands
Send command to pane with `tmux send-keys -t "session:window.pane" "command" Enter`. The Enter at end simulates pressing enter key. Target format is `session:window.pane` where pane is 0-indexed. Example: `tmux send-keys -t "main:dev.0" "yarn start" Enter`.

Stopping Processes
Send Ctrl+C to stop process with `tmux send-keys -t "session:window.pane" C-c`. No Enter needed after C-c. Wait briefly then capture pane to verify process stopped. Example workflow: send C-c, sleep 1, capture pane output.

Capturing Output
Capture pane output with `tmux capture-pane -t "session:window.pane" -p`. Add `| tail -N` to get last N lines. Use `-S -N` flag to capture N lines of scrollback. Example: `tmux capture-pane -t "main:dev.0" -p -S -50 | tail -30` captures last 50 lines, shows 30.

Dev Server Workflow
1. List windows to find dev server pane: `tmux list-windows -a`
2. Identify pane with `list-panes` and format string
3. Stop current process: `send-keys ... C-c`
4. Verify stopped by capturing output
5. Start new process: `send-keys ... "yarn start" Enter`
6. Verify started by capturing output after delay

Best Practices
Always verify target pane before sending commands. Capture output before and after operations. Use sleep/delay between stop and start commands. Check pane current_command to confirm expected state. Never assume pane state - always verify.

Common Targets
Format: `session:window.pane`. Window can be name or index. Pane is 0-indexed. If only one pane in window, `.0` can be omitted. Session name must match exactly.

Error Recovery
If command not executing check target path exists with list-windows/list-panes. If process not stopping try multiple C-c sends. If output garbled use -J flag for wrapped lines: `tmux capture-pane -t target -p -J`.
