#!/usr/bin/env bash

LINUX_ONLY_TEST_ROOTS_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/linux-only-test-roots.txt"

_discover_test_files() {
	local discoveryPolicy="$1"
	local pathPattern="$2"

	local -a prunedDirectoryExpression=(
		-path '*/.git'
		-o -path '*/node_modules'
		-o -path '*/private-configuration'
		-o -path '*/result'
		-o -path '*/result-*'
		-o -path '*/.deep-work'
		-o -path '*/.direnv'
		-o -path '*/.worktrees'
		-o -path '*/__pycache__'
	)

	if [[ "$discoveryPolicy" == "platform-scoped" && "$(uname)" == "Darwin" ]]; then
		local linuxOnlyTestRoot
		while read -r linuxOnlyTestRoot; do
			[[ -n "$linuxOnlyTestRoot" ]] || continue
			prunedDirectoryExpression+=(-o -path "$REPO_DIR/$linuxOnlyTestRoot")
		done <"$LINUX_ONLY_TEST_ROOTS_FILE"
	fi

	find "$REPO_DIR" \
		\( "${prunedDirectoryExpression[@]}" \) -prune -o \
		-path "$pathPattern" -type f -print 2>/dev/null | sort
}
