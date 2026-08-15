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

# A machine without the desktop toolchain still gets a useful quick tier, so a missing tool skips.
# CI sets QMLLINT_REQUIRED, where a skip would be indistinguishable from a passing lint and would
# report coverage the run never had.
_qmllint_unavailable() {
	if [[ -n "${QMLLINT_REQUIRED:-}" ]]; then
		echo "QML lint required but unavailable: $1" >&2
		return 1
	fi

	echo "SKIP: $1, skipping QML lint" >&2
	return 0
}

_run_qmllint_checks() {
	local qtDeclarativePath
	qtDeclarativePath="${QT_DECLARATIVE_PATH:-$(nix eval nixpkgs#qt6.qtdeclarative.outPath 2>/dev/null | tr -d '"')}"
	local qmllintBin="$qtDeclarativePath/bin/qmllint"

	if [[ ! -x "$qmllintBin" ]]; then
		_qmllint_unavailable "qmllint not found at $qmllintBin"
		return $?
	fi

	if ! command -v quickshell &>/dev/null; then
		_qmllint_unavailable "quickshell not installed"
		return $?
	fi

	# The upstream flake ships quickshell wrapped and nixpkgs ships it plain, so resolve the import
	# root by looking for the module tree itself rather than by matching one packaging's path name.
	local quickshellQmlPath=""
	local storePath
	while read -r storePath; do
		if [[ -d "$storePath/lib/qt-6/qml" ]]; then
			quickshellQmlPath="$storePath/lib/qt-6/qml"
			break
		fi
	done < <(nix-store -qR "$(command -v quickshell)" 2>/dev/null | grep quickshell)

	if [[ -z "$quickshellQmlPath" ]]; then
		_qmllint_unavailable "quickshell QML modules not found in its closure"
		return $?
	fi

	local qt5compatPath
	qt5compatPath="$(nix eval nixpkgs#qt6Packages.qt5compat.outPath 2>/dev/null | tr -d '"')/lib/qt-6/qml"

	echo "--- QML Lint ---"
	local qmlFiles
	qmlFiles=$(find "$REPO_DIR/machine-configuration/desktop/quickshell" -name "*.qml" -type f | sort)
	local failCount=0

	for qmlFile in $qmlFiles; do
		local errors
		errors=$("$qmllintBin" \
			-I "$qtDeclarativePath/lib/qt-6/qml" \
			-I "$quickshellQmlPath" \
			-I "$qt5compatPath" \
			--compiler warning \
			"$qmlFile" 2>&1 | grep -c "^Warning:" || true)
		if [[ "$errors" -gt 0 ]]; then
			failCount=$((failCount + errors))
		fi
	done

	local totalFiles
	totalFiles=$(echo "$qmlFiles" | wc -l)
	echo "  Checked $totalFiles QML files, $failCount warnings"
	echo ""

	if [[ "$failCount" -gt 0 ]]; then
		echo "QML lint: $failCount warning(s) across $totalFiles files" >&2
		return 1
	fi
}
