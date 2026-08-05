#!/usr/bin/env bash

# shellcheck source=runner/foreign-platform-test-roots.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/foreign-platform-test-roots.sh"

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

	if [[ "$discoveryPolicy" == "platform-scoped" ]]; then
		local foreignPlatformTestRoot
		while read -r foreignPlatformTestRoot; do
			prunedDirectoryExpression+=(-o -path "$REPO_DIR/$foreignPlatformTestRoot")
		done < <(_foreign_platform_test_roots)
	fi

	find "$REPO_DIR" \
		\( "${prunedDirectoryExpression[@]}" \) -prune -o \
		-path "$pathPattern" -type f -print 2>/dev/null | sort
}
