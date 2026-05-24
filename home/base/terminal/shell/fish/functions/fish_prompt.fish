function fish_prompt
  if test -n "$DEVENV_ROOT"
    set_color red
    printf '(devenv)'
    set_color normal
  end

  set_color --bold green
  printf ' %s ' (whoami)
  set_color --bold blue
  printf '%s' (prompt_pwd)
  set_color --bold yellow
  printf '%s' (fish_git_prompt)
  set_color normal
  printf '$ '
end 
