#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
# shellcheck disable=SC2016 # The inner Bash intentionally expands these variables.
python3 run.py /bin/bash -c '
set -eu
nix --version
home-manager --version
git --version
gh --version | head -1
ssh -V
age --version
jq --version
rg --version | head -1
fd --version
bat --version
fzf --version
zoxide --version
tmux -V
python3 --version
node --version
nixfmt --version
media-speech --help >/dev/null
test "$(git config --get init.defaultBranch)" = main
test -L "$HOME/.bashrc"
test -L "$HOME/.config/git/config"
test -L "$HOME/.config/tmux/tmux.conf"
test ! -w /etc
test "$(nix config show sandbox)" = true
test "$(nix config show sandbox-fallback)" = false
printf "All runtime and configuration checks passed.\n"
'
# shellcheck disable=SC2016 # The managed login shell expands these variables.
python3 run.py bash -lc '
set -eu
case "$(command -v nix)" in "$HOME/.nix-profile/bin/nix") ;; *) exit 1 ;; esac
case "$(command -v git)" in "$HOME/.nix-profile/bin/git") ;; *) exit 1 ;; esac
nix --version
home-manager --version
media-speech --help >/dev/null
jq --version
git --version
printf "Managed login-shell PATH checks passed.\n"
'
