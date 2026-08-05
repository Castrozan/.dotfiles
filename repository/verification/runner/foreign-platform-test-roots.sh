#!/usr/bin/env bash

_foreign_platform_test_roots_file() {
	local testRootsDirectory
	testRootsDirectory="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
	if [[ "$(uname)" == "Darwin" ]]; then
		echo "$testRootsDirectory/linux-only-test-roots.txt"
	else
		echo "$testRootsDirectory/darwin-only-test-roots.txt"
	fi
}

_foreign_platform_test_roots() {
	local foreignPlatformTestRoot
	while read -r foreignPlatformTestRoot; do
		[[ -n "$foreignPlatformTestRoot" ]] || continue
		echo "$foreignPlatformTestRoot"
	done <"$(_foreign_platform_test_roots_file)"
}
