function fish_prompt
  set_color green
  printf ' %s ' (whoami)
  set_color blue
  printf '%s' (prompt_pwd)
  set_color yellow
  printf '%s' (fish_git_prompt)
  set_color normal
  printf '$ '
end 
