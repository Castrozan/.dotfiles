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

  # Manually set environment variables that don't transfer cleanly
  set -gx EDITOR cursor
  set -gx PNPM_HOME ~/.local/share/pnpm
  fish_add_path ~/.local/bin
  fish_add_path ~/.pyenv/bin
  fish_add_path $PNPM_HOME

  # Set Obsidian vault path if it exists
  if test -d ~/vault
    set -gx OBSIDIAN_HOME ~/vault
  end
end

__load_bash_env
