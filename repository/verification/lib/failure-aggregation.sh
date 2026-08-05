#!/usr/bin/env bash

_run_checks_reporting_every_failure() {
	local -a failedChecks=()
	local checkFunction
	local checkCount=$#

	for checkFunction in "$@"; do
		"$checkFunction" || failedChecks+=("$checkFunction")
	done

	if [[ ${#failedChecks[@]} -eq 0 ]]; then
		return 0
	fi

	echo "=== ${#failedChecks[@]} of ${checkCount} checks failed ==="
	for checkFunction in "${failedChecks[@]}"; do
		echo "  FAILED: ${checkFunction#_run_}"
	done
	echo "Every check above already ran, so fix all of these in one pass." >&2
	return 1
}
