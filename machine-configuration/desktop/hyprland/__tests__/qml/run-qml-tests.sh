#!/usr/bin/env bash

set -Eeuo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly MOCKS_DIR="$SCRIPT_DIR/mocks"
readonly QT_DECLARATIVE_PATH="${QT_DECLARATIVE_PATH:-$(nix eval nixpkgs#qt6.qtdeclarative.outPath 2>/dev/null | tr -d '"')}"
readonly QMLTESTRUNNER="$QT_DECLARATIVE_PATH/bin/qmltestrunner"
readonly QT_QML_PATH="$QT_DECLARATIVE_PATH/lib/qt-6/qml"

main() {
	if [[ ! -x "$QMLTESTRUNNER" ]]; then
		echo "SKIP: qmltestrunner not found at $QMLTESTRUNNER" >&2
		return 0
	fi

	local testFiles
	testFiles=$(find "$SCRIPT_DIR" -maxdepth 1 -name "tst_*.qml" -type f | sort)

	if [[ -z "$testFiles" ]]; then
		echo "No QML test files found in $SCRIPT_DIR"
		return 0
	fi

	local failedTests=0
	local passedTests=0

	for testFile in $testFiles; do
		local testName
		testName="$(basename "$testFile" .qml)"
		echo "  QML: $testName"

		if QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software \
			"$QMLTESTRUNNER" \
			-input "$testFile" \
			-import "$QT_QML_PATH" \
			-import "$MOCKS_DIR" 2>&1; then
			passedTests=$((passedTests + 1))
		else
			echo "  FAIL: $testName"
			failedTests=$((failedTests + 1))
		fi
	done

	echo "QML tests: $passedTests passed, $failedTests failed"

	if [[ "$failedTests" -gt 0 ]]; then
		return 1
	fi
}

main "$@"
