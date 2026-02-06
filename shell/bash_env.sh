#!/usr/bin/env bash

# Shared environment for bash + fish (via `bass`).
# Keep this file fast to source. Anything expensive should be lazy-loaded.

# Add local bin to PATH
export PATH="$PATH:$HOME/.local/bin"

# Neovim (TODO: fix if this path is not valid on a given machine)
export PATH="$PATH:/opt/nvim-linux64/bin"

# Pyenv
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"

# flatpak
export XDG_DATA_DIRS="/var/lib/flatpak/exports/share:$HOME/.local/share/flatpak/exports/share:${XDG_DATA_DIRS:-}"

# pnpm
export PNPM_HOME="$HOME/.local/share/pnpm"
case ":$PATH:" in
  *":$PNPM_HOME:"*) ;;
  *) export PATH="$PNPM_HOME:$PATH" ;;
esac

# cargo
if [ -d "$HOME/.cargo/bin" ]; then
  case ":$PATH:" in
    *":$HOME/.cargo/bin:"*) ;;
    *) export PATH="$HOME/.cargo/bin:$PATH" ;;
  esac
fi
