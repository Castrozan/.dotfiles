if test -f /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.fish
    source /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.fish
end

set -gx BASH_ENV "$HOME/.dotfiles/home/modules/terminal/shell/aliases.sh"

set -gx PYENV_ROOT $HOME/.pyenv
set -gx PNPM_HOME $HOME/.local/share/pnpm

fish_add_path $HOME/.local/bin
fish_add_path $PYENV_ROOT/bin
fish_add_path $PNPM_HOME

if test -d /var/lib/flatpak/exports/share
    set -gx XDG_DATA_DIRS "/var/lib/flatpak/exports/share:$HOME/.local/share/flatpak/exports/share:$XDG_DATA_DIRS"
end
