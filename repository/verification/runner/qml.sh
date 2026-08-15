#!/usr/bin/env bash

_run_qml_unit_tests() {
	local qmlTestDirs
	qmlTestDirs=$(_discover_test_files "cross-platform" "*/__tests__/qml/run-qml-tests.sh")

	if [[ -z "$qmlTestDirs" ]]; then
		return 0
	fi

	echo "--- QML Unit Tests ---"
	local failedRunners=0
	for runner in $qmlTestDirs; do
		bash "$runner" || failedRunners=$((failedRunners + 1))
	done
	echo ""

	if [[ "$failedRunners" -gt 0 ]]; then
		echo "QML unit tests: $failedRunners runner(s) failed" >&2
		return 1
	fi
}

_skip_qmllint_unless_required() {
	if [[ -n "${QMLLINT_REQUIRED:-}" ]]; then
		echo "QML lint required but unavailable: $1" >&2
		return 1
	fi

	echo "SKIP: $1, skipping QML lint" >&2
	return 0
}

_quickshell_qml_import_root_from_closure() {
	local storePath
	while read -r storePath; do
		if [[ -d "$storePath/lib/qt-6/qml" ]]; then
			echo "$storePath/lib/qt-6/qml"
			return 0
		fi
	done < <(nix-store -qR "$(command -v quickshell)" 2>/dev/null | grep quickshell)

	return 1
}

_print_qmllint_categories_if_any() {
	grep -oE '\[[a-z0-9.-]+\]$' "$1" | sort | uniq -c | sort -rn | head -8 | sed 's/^/  /' || true
}

_qmllint_baseline_file() {
	echo "$REPO_DIR/repository/verification/qmllint-baseline.json"
}

_grandfathered_qmllint_warning_ceiling() {
	local recordedCeiling
	recordedCeiling=$(grep -oE '"maxWarnings"[[:space:]]*:[[:space:]]*[0-9]+' "$(_qmllint_baseline_file)" 2>/dev/null | grep -oE '[0-9]+$')
	echo "${recordedCeiling:-0}"
}

_run_qmllint_checks() {
	local qtDeclarativePath
	qtDeclarativePath="${QT_DECLARATIVE_PATH:-$(nix eval nixpkgs#qt6.qtdeclarative.outPath 2>/dev/null | tr -d '"')}"
	local qmllintBin="$qtDeclarativePath/bin/qmllint"

	if [[ ! -x "$qmllintBin" ]]; then
		_skip_qmllint_unless_required "qmllint not found at $qmllintBin"
		return $?
	fi

	if ! command -v quickshell &>/dev/null; then
		_skip_qmllint_unless_required "quickshell not installed"
		return $?
	fi

	local quickshellQmlPath
	if ! quickshellQmlPath="$(_quickshell_qml_import_root_from_closure)"; then
		_skip_qmllint_unless_required "quickshell QML modules not found in its closure"
		return $?
	fi

	local qt5compatPath
	qt5compatPath="$(nix eval nixpkgs#qt6Packages.qt5compat.outPath 2>/dev/null | tr -d '"')/lib/qt-6/qml"

	echo "--- QML Lint ---"
	local qmlFiles
	qmlFiles=$(find "$REPO_DIR/machine-configuration/desktop/quickshell" -name "*.qml" -type f | sort)

	local warningLog
	warningLog="$(mktemp)"

	local qmlFile
	for qmlFile in $qmlFiles; do
		"$qmllintBin" \
			-I "$qtDeclarativePath/lib/qt-6/qml" \
			-I "$quickshellQmlPath" \
			-I "$qt5compatPath" \
			--compiler warning \
			"$qmlFile" 2>&1 | grep "^Warning:" >>"$warningLog" || true
	done

	local warningCount totalFiles
	warningCount=$(wc -l <"$warningLog" | tr -d ' ')
	totalFiles=$(echo "$qmlFiles" | wc -l)

	echo "  Checked $totalFiles QML files, $warningCount warnings"
	echo "  Warnings by category:"
	_print_qmllint_categories_if_any "$warningLog"
	rm -f "$warningLog"
	echo ""

	local warningCeiling
	warningCeiling="$(_grandfathered_qmllint_warning_ceiling)"

	if [[ "$warningCount" -gt "$warningCeiling" ]]; then
		echo "QML lint: $warningCount warnings across $totalFiles files, above the baseline of $warningCeiling" >&2
		echo "Fix the new warnings, or raise maxWarnings in $(_qmllint_baseline_file) if the growth is intended." >&2
		return 1
	fi

	if [[ "$warningCount" -lt "$warningCeiling" ]]; then
		echo "  Below the baseline of $warningCeiling: lower maxWarnings to $warningCount to hold the gain"
		echo ""
	fi
}
