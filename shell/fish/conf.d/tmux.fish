function __start_tmux
  if not command -v tmux > /dev/null
    return
  end

  tmux has-session -t screensaver 2>/dev/null || begin
    tmux new-session -d -s screensaver -n screensaver
    tmux send-keys -t screensaver 'bonsai_screensaver' Enter
    tmux split-window -h -t screensaver
    tmux send-keys -t screensaver.1 'pipes_screensaver' Enter
    if command -v cmatrix > /dev/null
      tmux split-window -v -t screensaver
      tmux send-keys -t screensaver.2 'sleep 1; cmatrix -U "🎄,⭐,🎁,🔔" -F 10' Enter
      tmux select-pane -t 1
    else
      tmux select-pane -t 1
    end
  end

  tmux has-session -t main 2>/dev/null || tmux new-session -d -s main

  if [ -z "$TMUX" ] && ! string match -q "*cursor*" (ps -o comm= -p $fish_pid)
    tmux attach -t screensaver
  end
end

if status is-interactive && [ "$TERM" != "dumb" ]
  __start_tmux
end 
