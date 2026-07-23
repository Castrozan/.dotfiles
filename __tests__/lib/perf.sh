#!/usr/bin/env bash

_run_rebuild_baseline_check() {
	if ! command -v benchmark-rebuild &>/dev/null; then
		echo "SKIP: benchmark-rebuild not installed" >&2
		return 0
	fi

	echo "--- Rebuild Performance Baseline Check ---"
	benchmark-rebuild --check-baseline
	echo ""
}

_run_desktop_baseline_check() {
	if ! command -v benchmark-desktop &>/dev/null; then
		echo "SKIP: benchmark-desktop not installed" >&2
		return 0
	fi

	echo "--- Desktop Performance Baseline Check ---"
	benchmark-desktop --check-baseline
	echo ""
}

_run_perf_tier() {
	echo "--- Desktop Benchmarks ---"
	if command -v benchmark-desktop &>/dev/null; then
		benchmark-desktop 3
	else
		echo "SKIP: benchmark-desktop not installed" >&2
	fi
	echo ""

	_run_desktop_baseline_check
	_run_rebuild_baseline_check

	echo "--- Shell Benchmarks ---"
	if command -v benchmark-shell &>/dev/null; then
		benchmark-shell 3
	else
		echo "SKIP: benchmark-shell not installed" >&2
	fi
	echo ""

	echo "--- Performance Threshold Tests ---"
	local -a perfTests
	mapfile -t perfTests < <(find "$REPO_DIR/home/base" "$REPO_DIR/home/linux" "$REPO_DIR/home/darwin" -name "perf-runtime.bats" -type f 2>/dev/null | sort)
	if [[ ${#perfTests[@]} -gt 0 ]] && command -v bats &>/dev/null; then
		bats "${perfTests[@]}"
	else
		echo "SKIP: no perf-runtime.bats files or bats not installed" >&2
	fi
	echo ""
}
