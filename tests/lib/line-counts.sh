#!/usr/bin/env bash

_run_line_count_check() {
	if ! command -v python3 &>/dev/null; then
		echo "WARN: python3 not installed, skipping line-count check" >&2
		return 0
	fi

	echo "--- Line Count Policy ---"
	python3 "$SCRIPT_DIR/check-line-counts.py"
	echo ""
}
