function __load_bash_env
  # Source the most appropriate bashrc if available
  set -l bashrc_path
  if test -f ~/.bashrc
    set bashrc_path ~/.bashrc
  else if test -f /etc/bashrc
    set bashrc_path /etc/bashrc
  end

  if test -n "$bashrc_path"; and type -q bass
    bass source $bashrc_path
  end

  # TODO: move this to appropriate place
  set -gx PNPM_HOME ~/.local/share/pnpm
  fish_add_path ~/.local/bin
  fish_add_path ~/.pyenv/bin
  fish_add_path $PNPM_HOME
end

__load_bash_env
