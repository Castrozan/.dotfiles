#!/usr/bin/env bash

_other_platform_home_directory_to_exclude() {
	if [[ "$(uname)" == "Darwin" ]]; then
		echo "$REPO_DIR/home/linux"
	else
		echo "$REPO_DIR/home/darwin"
	fi
}

_discover_test_files() {
	local discoveryPolicy="$1"
	local pathPattern="$2"

	local -a prunedDirectoryExpression=(
		-path '*/.git'
		-o -path '*/node_modules'
		-o -path '*/private-config'
		-o -path '*/result'
		-o -path '*/result-*'
		-o -path '*/.deep-work'
		-o -path '*/.direnv'
		-o -path '*/.worktrees'
		-o -path '*/__pycache__'
	)

	if [[ "$discoveryPolicy" == "platform-scoped" ]]; then
		prunedDirectoryExpression+=(-o -path "$(_other_platform_home_directory_to_exclude)")
	fi

	find "$REPO_DIR" \
		\( "${prunedDirectoryExpression[@]}" \) -prune -o \
		-path "$pathPattern" -type f -print 2>/dev/null | sort
}
