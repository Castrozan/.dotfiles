---
name: tmux
description: Tmux session and process control. Use when restarting dev servers, checking process output, stopping/starting background processes, or managing services in tmux panes.
---
<!-- @agent-architect owns this file. Delegate changes, don't edit directly. -->

# Tmux Interaction

Control processes in tmux sessions from AI agents.

## Session Discovery

List all windows across sessions:
```bash
tmux list-windows -a
```
Output format: `session:window: window_name (n panes) [geometry] [flags]`

## Pane Discovery

List panes in specific window:
```bash
tmux list-panes -t "session:window" -F "#{pane_index}: #{pane_current_command} - #{pane_current_path}"
```
Shows pane index, running command, and working directory.

## Sending Commands

Send command to pane:
```bash
tmux send-keys -t "session:window.pane" "command" Enter
```
Target format: `session:window.pane` (pane is 0-indexed). Example: `tmux send-keys -t "main:dev.0" "yarn start" Enter`

## Stopping Processes

Send Ctrl+C:
```bash
tmux send-keys -t "session:window.pane" C-c
```
No Enter needed after C-c. Wait briefly then capture pane to verify process stopped.

## Capturing Output

Capture pane output:
```bash
tmux capture-pane -t "session:window.pane" -p
```
Add `| tail -N` for last N lines. Use `-S -N` for N lines of scrollback. Example: `tmux capture-pane -t "main:dev.0" -p -S -50 | tail -30`

## Dev Server Restart Workflow

1. List windows to find dev server pane: `tmux list-windows -a`
2. Identify pane: `tmux list-panes -t "session:window" -F "#{pane_index}: #{pane_current_command}"`
3. Stop process: `tmux send-keys -t "session:window.pane" C-c`
4. Verify stopped by capturing output
5. Start new process: `tmux send-keys -t "session:window.pane" "yarn start" Enter`
6. Verify started by capturing output after delay

## Target Format

Format: `session:window.pane`
- Window can be name or index
- Pane is 0-indexed
- If only one pane in window, `.0` can be omitted
- Session name must match exactly

## Error Recovery

| Problem | Solution |
|---------|----------|
| Command not executing | Verify target exists with list-windows/list-panes |
| Process not stopping | Try multiple C-c sends |
| Output garbled | Use -J flag: `tmux capture-pane -t target -p -J` |

## Best Practices

- Always verify target pane before sending commands
- Capture output before and after operations
- Use sleep/delay between stop and start commands
- Check pane current_command to confirm expected state
- Never assume pane state - always verify
