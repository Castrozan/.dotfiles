function __load_bash_env
  # Source only the portable parts of .bashrc
  bass source ~/.bashrc

  # Manually set environment variables that don't transfer cleanly
  set -gx EDITOR cursor
  set -gx PNPM_HOME ~/.local/share/pnpm
  fish_add_path ~/.local/bin
  fish_add_path ~/.pyenv/bin
  fish_add_path $PNPM_HOME
end

__load_bash_env 
