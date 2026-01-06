# Per-Pane Command Timing Handoff

## Goal
Display elapsed time (HH:MM:SS) for running commands in tmux pane borders, using Catppuccin theme.

## Current State

### Working Components
- **Shell hooks**: Bash (`shell/bash_tmux_timing.sh`) and Fish (`shell/fish/conf.d/tmux_timing.fish`) set `pane_cmd_start` pane option per command
- **Hooks integrated**: `.bashrc` sources bash hook, `shell/fish/config.fish` sources fish hook
- **Flake builds**: No errors

### Configuration Files
- `.config/tmux/settings.conf`: Basic tmux settings, `status-interval 1` set
- `.config/tmux/catppuccin.conf`: Catppuccin theme config with `@catppuccin_pane_status_enabled "yes"` and `@catppuccin_pane_border_status "top"`
- `home/modules/tmux.nix`: Loads settings, binds, and catppuccin config

### Problem
Timer not appearing in pane borders. Catppuccin manages pane border display via `@catppuccin_pane_default_text`. Need to integrate timer into Catppuccin's pane border format without breaking theme.

## Required Solution
Modify Catppuccin pane border to show: `#{pane_current_path} #{?pane_cmd_start,⏱ HH:MM:SS,}` when command is running.

## Key Constraints
- Catppuccin theme controls pane borders via `@catppuccin_pane_default_text`
- `pane_cmd_start` is set per-pane by shell hooks
- Must preserve Catppuccin styling
- tmux version may not support `pane-active-border-format`

## Files to Modify
- `.config/tmux/catppuccin.conf`: Update `@catppuccin_pane_default_text` to include timer
- Possibly `.config/tmux/settings.conf`: Ensure `pane-border-status top` is set

maybe try something like this


To track the elapsed time of a command as it is running in Linux, the most direct approach is to use the ps or top commands to monitor the existing process, or use the watch command to periodically execute a time-tracking command. 
Method 1: Using ps (Process Status)
The ps command can display the elapsed time (etime) since a process was started. This method is useful for a command that is already running in the background or a different terminal. 
Find the Process ID (PID) of your running command using pgrep or pidof, or by inspecting the output of ps -e.
bash
pgrep <command_name>
(e.g., pgrep my_script.sh)
Use ps with the etime option and the PID to view the elapsed time.
bash
ps -p <PID> -o etime=
The output format will be [[DD-]hh:]mm:ss, where DD is days, hh is hours, mm is minutes, and ss is seconds. 
Method 2: Using top or htop
The top command (or the more user-friendly htop) provides a real-time, interactive overview of running processes. 
Run top in your terminal.
Press the f key and select the ELAPSED or TIME+ column to ensure it is visible, then press q to return to the main view (or c in top to toggle some display options).
The TIME+ column displays the accumulated CPU time for each process, giving you an idea of its duration. 
Method 3: Using watch for Periodic Monitoring
The watch command can be used to repeatedly run another command and display its output, which helps in monitoring changes over time. You can combine this with ps to see the updating elapsed time of a process. 
bash
watch -n 1 'ps -p <PID> -o etime='
This command will update the elapsed time output for the specified PID every 1 second (-n 1). 