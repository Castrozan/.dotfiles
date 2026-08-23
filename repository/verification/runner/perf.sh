#!/usr/bin/env bash

_validate_tracked_baseline_from_source() {
	local benchmarkSource="$1"
	shift
	local capabilityDirectory="$REPO_DIR/machine-configuration/development/testing"

	PYTHONPATH="$capabilityDirectory/scripts/lib${PYTHONPATH:+:$PYTHONPATH}" \
		DOTFILES_BENCHMARK_CHECKOUT="$REPO_DIR" \
		python3 "$capabilityDirectory/scripts/$benchmarkSource" --check-baseline "$@"
}

_run_rebuild_baseline_check() {
	echo "--- Rebuild Performance Baseline Check ---"
	local baselineExitCode=0
	_validate_tracked_baseline_from_source benchmark_rebuild.py "$@" || baselineExitCode=$?
	echo ""
	return "$baselineExitCode"
}

_run_desktop_baseline_check() {
	echo "--- Desktop Performance Baseline Check ---"
	local baselineExitCode=0
	_validate_tracked_baseline_from_source benchmark_desktop.py "$@" || baselineExitCode=$?
	echo ""
	return "$baselineExitCode"
}

_run_perf_tier() {
	echo "--- Desktop Benchmarks ---"
	if command -v benchmark-desktop &>/dev/null; then
		benchmark-desktop 3
	else
		echo "SKIP: benchmark-desktop not installed" >&2
	fi
	echo ""

	_run_desktop_baseline_check --require-fresh
	_run_rebuild_baseline_check --require-fresh

	echo "--- Shell Benchmarks ---"
	if command -v benchmark-shell &>/dev/null; then
		benchmark-shell 3
	else
		echo "SKIP: benchmark-shell not installed" >&2
	fi
	echo ""

	echo "--- Performance Threshold Tests ---"
	local -a perfTests=()
	local discoveredPerfTest
	while IFS= read -r discoveredPerfTest; do
		perfTests+=("$discoveredPerfTest")
	done < <(_discover_test_files "platform-scoped" "*/__tests__/e2e/perf-runtime.bats")
	if [[ ${#perfTests[@]} -gt 0 ]] && command -v bats &>/dev/null; then
		bats "${perfTests[@]}"
	else
		echo "SKIP: no perf-runtime.bats files or bats not installed" >&2
	fi
	echo ""
}
