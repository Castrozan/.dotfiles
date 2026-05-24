#!/usr/bin/env bash

_collect_quick_pytest_test_files() {
	find "$REPO_DIR/home/base" "$REPO_DIR/home/linux" "$REPO_DIR/home/darwin" "$REPO_DIR/agents/hooks" "$REPO_DIR/agents/skills" "$REPO_DIR/tests" -path "*/tests/test_*.py" -type f | sort
}

_run_quick_pytest_tests() {
	if ! command -v pytest &>/dev/null; then
		echo "WARN: pytest not installed, skipping python tests" >&2
		return 0
	fi

	local testFiles
	testFiles=$(_collect_quick_pytest_test_files)
	if [[ -z "$testFiles" ]]; then
		return 0
	fi

	echo "--- Python Tests (quick) ---"
	pytest $testFiles -x -q
	echo ""
}
