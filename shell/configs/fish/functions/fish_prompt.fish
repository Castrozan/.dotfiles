function fish_prompt
  set_color --bold green
  printf ' %s ' (whoami)
  set_color --bold blue
  printf '%s' (prompt_pwd)
  set_color --bold yellow
  printf '%s' (fish_git_prompt)
  set_color normal
  printf '$ '
end 
