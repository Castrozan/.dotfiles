#!/usr/bin/env bash

if [ -n "${TMUX:-}" ]; then
	export TERM=tmux-256color
fi

export _ZO_FZF_OPTS="--height 40% \
--layout=reverse --border --preview='command -p ls -ACp \
--color=always --group-directories-first {2..}' \
--preview-window=right,50%,sharp \
--color=bg+:#313244,bg:#1e1e2e,spinner:#f5e0dc,hl:#f38ba8 \
--color=fg:#cdd6f4,header:#f38ba8,info:#cba6f7,pointer:#f5e0dc \
--color=marker:#b4befe,fg+:#cdd6f4,prompt:#cba6f7,hl+:#f38ba8 \
--color=selected-bg:#45475a \
--multi"

_bash_interactive_shell_directory="$HOME/.dotfiles/home/base/terminal/shell"

for _bash_interactive_source_file in \
	bash_env.sh \
	bash_history.sh \
	aliases.sh \
	fzf_catppuccin_theme.sh \
	default_directories.sh \
	bash_prompt.sh \
	bash_hyprland_env.sh \
	bash_tmux_autostart.sh; do
	if [ -r "$_bash_interactive_shell_directory/$_bash_interactive_source_file" ]; then
		. "$_bash_interactive_shell_directory/$_bash_interactive_source_file"
	fi
done

unset _bash_interactive_source_file _bash_interactive_shell_directory
