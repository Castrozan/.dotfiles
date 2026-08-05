#!/usr/bin/env bash

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

	if [[ "$discoveryPolicy" == "platform-scoped" && "$(uname)" == "Darwin" ]]; then
		prunedDirectoryExpression+=(-o -path "$REPO_DIR/home/linux")
	fi

	find "$REPO_DIR" \
		\( "${prunedDirectoryExpression[@]}" \) -prune -o \
		-path "$pathPattern" -type f -print 2>/dev/null | sort
}
