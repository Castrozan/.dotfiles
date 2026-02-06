function __start_tmux
  if not command -v tmux > /dev/null
    return
  end

  # Check if sessions already exist to avoid recreating
  if not tmux has-session -t screensaver 2>/dev/null
    if type -q bash
      # Use bash directly in background to prevent blocking
      bash -c '
        source ~/.dotfiles/shell/screensaver.sh 2>/dev/null || true
        source ~/.dotfiles/shell/tmux_main.sh 2>/dev/null || true
        _start_screensaver_tmux_session 2>/dev/null || true
        _start_main_tmux_session 2>/dev/null || true
      ' &
    end
  end

  if [ -z "$TMUX" ] && ! string match -q "*cursor*" (ps -o comm= -p $fish_pid)
    tmux attach -t screensaver 2>/dev/null
  end
end

# Wrapper function for bass-translated bash alias compatibility
function _start_tmux
  __start_tmux $argv
end

if status is-interactive && [ "$TERM" != "dumb" ]
  __start_tmux
end
