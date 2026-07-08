#!/usr/bin/env bash

_prompt_abbreviated_working_directory() {
	local path_with_home_tilde="${PWD/#$HOME/\~}"
	local -a path_segments
	local IFS=/
	read -r -a path_segments <<<"$path_with_home_tilde"
	local segment_count=${#path_segments[@]}
	local rendered=""
	local segment_index
	for ((segment_index = 0; segment_index < segment_count; segment_index++)); do
		local segment="${path_segments[segment_index]}"
		if [ "$segment_index" -eq "$((segment_count - 1))" ] || [ -z "$segment" ]; then
			rendered+="$segment"
		else
			rendered+="${segment:0:1}"
		fi
		if [ "$segment_index" -lt "$((segment_count - 1))" ]; then
			rendered+="/"
		fi
	done
	printf '%s' "$rendered"
}

_prompt_git_branch() {
	local branch
	branch=$(git symbolic-ref --short HEAD 2>/dev/null) || return
	printf ' (%s)' "$branch"
}

_prompt_devenv_marker() {
	if [ -n "${DEVENV_ROOT:-}" ]; then
		printf '(devenv)'
	fi
}

PS1='\[\e[31m\]$(_prompt_devenv_marker)\[\e[1;32m\] \u \[\e[1;34m\]$(_prompt_abbreviated_working_directory)\[\e[1;33m\]$(_prompt_git_branch)\[\e[0m\]$ '
