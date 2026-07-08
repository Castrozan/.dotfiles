#!/usr/bin/env bash

if [ -n "${TMUX:-}" ]; then
	export TERM=tmux-256color
fi

_bash_interactive_shell_directory="$HOME/.dotfiles/home/base/terminal/shell"

for _bash_interactive_source_file in \
	bash_env.sh \
	aliases.sh \
	fzf_catppuccin_theme.sh \
	default_directories.sh \
	bash_prompt.sh \
	bash_tmux_autostart.sh; do
	if [ -r "$_bash_interactive_shell_directory/$_bash_interactive_source_file" ]; then
		. "$_bash_interactive_shell_directory/$_bash_interactive_source_file"
	fi
done

unset _bash_interactive_source_file _bash_interactive_shell_directory
