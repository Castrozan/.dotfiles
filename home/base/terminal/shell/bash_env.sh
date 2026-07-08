#!/usr/bin/env bash

case ":$PATH:" in
*":$HOME/.local/bin:"*) ;;
*) export PATH="$PATH:$HOME/.local/bin" ;;
esac

if [ -d /opt/nvim-linux64/bin ]; then
	case ":$PATH:" in
	*":/opt/nvim-linux64/bin:"*) ;;
	*) export PATH="$PATH:/opt/nvim-linux64/bin" ;;
	esac
fi

export PYENV_ROOT="$HOME/.pyenv"
case ":$PATH:" in
*":$PYENV_ROOT/bin:"*) ;;
*) export PATH="$PYENV_ROOT/bin:$PATH" ;;
esac

if [ -d /var/lib/flatpak ]; then
	export XDG_DATA_DIRS="/var/lib/flatpak/exports/share:$HOME/.local/share/flatpak/exports/share:${XDG_DATA_DIRS:-}"
fi

export PNPM_HOME="$HOME/.local/share/pnpm"
case ":$PATH:" in
*":$PNPM_HOME:"*) ;;
*) export PATH="$PNPM_HOME:$PATH" ;;
esac

if [ -d "$HOME/.cargo/bin" ]; then
	case ":$PATH:" in
	*":$HOME/.cargo/bin:"*) ;;
	*) export PATH="$HOME/.cargo/bin:$PATH" ;;
	esac
fi
