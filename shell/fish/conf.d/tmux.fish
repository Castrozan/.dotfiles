function __start_tmux
  if not command -v tmux > /dev/null
    return
  end

  if type -q bass
    bass 'source ~/.dotfiles/shell/screensaver.sh; source ~/.dotfiles/shell/tmux_main.sh; _start_screensaver_tmux_session; _start_main_tmux_session'
  end

  if [ -z "$TMUX" ] && ! string match -q "*cursor*" (ps -o comm= -p $fish_pid)
    tmux attach -t screensaver
  end
end

if status is-interactive && [ "$TERM" != "dumb" ]
  __start_tmux
end 
