#!/usr/bin/env bash

z() {
	if [[ $# -eq 0 || $1 == -* || ($# -eq 1 && -d $1) || ${*: -1} == "${__zoxide_z_prefix?}"?* ]]; then
		__zoxide_z "$@"
		return $?
	fi
	local directory_keyword
	for directory_keyword in "$@"; do
		if [[ $directory_keyword == */* ]]; then
			__zoxide_z "$@"
			return $?
		fi
	done
	__zoxide_doctor
	local directory_query_output directory_query_status=0
	directory_query_output=$(command zoxide query --exclude "$(__zoxide_pwd)" -- "$@" 2>&1) || directory_query_status=$?
	if [[ $directory_query_status -eq 0 ]]; then
		__zoxide_cd "$directory_query_output"
	elif [[ $directory_query_output == 'zoxide: no match found' ]]; then
		cx "$@"
	else
		printf '%s\n' "$directory_query_output" >&2
		return "$directory_query_status"
	fi
}
