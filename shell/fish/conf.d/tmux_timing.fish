# Per-pane command timing for tmux
# Sets pane-local tmux option to track command execution time
# Timer is displayed in tmux status bar via settings.conf

function __tmux_cmd_start --on-event fish_preexec
  if set -q TMUX
    tmux set-option -p pane_cmd_start (date +%s) >/dev/null 2>&1
  end
end

function __tmux_cmd_end --on-event fish_prompt
  if set -q TMUX
    tmux set-option -p -u pane_cmd_start >/dev/null 2>&1
  end
end

