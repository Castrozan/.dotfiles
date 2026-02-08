function __load_bash_env
  # Source nix-daemon for Nix package manager
  if test -f /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.fish
    source /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.fish
  end

  # Export BASH_ENV for non-interactive bash (Claude Code)
  set -gx BASH_ENV "$HOME/.dotfiles/shell/aliases.sh"

  # Keep fish startup fast by importing a shared, fast-to-source bash env file.
  # Single source-of-truth pattern:
  # - bash: source this from ~/.bashrc (and keep ~/.bashrc lean)
  # - fish: import it via bass
  if type -q bass
    bass source "$HOME/.dotfiles/shell/bash_env.sh"
  end

  # TODO: move this to appropriate place
  set -gx PNPM_HOME ~/.local/share/pnpm
  fish_add_path ~/.local/bin
  fish_add_path ~/.pyenv/bin
  fish_add_path $PNPM_HOME
end

__load_bash_env
