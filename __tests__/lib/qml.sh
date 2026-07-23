#!/usr/bin/env bash

_run_qml_unit_tests() {
	local qmlTestDirs
	qmlTestDirs=$(find "$REPO_DIR/home/base" "$REPO_DIR/home/linux" "$REPO_DIR/home/darwin" -path "*/__tests__/qml/run-qml-tests.sh" -type f | sort)

	if [[ -z "$qmlTestDirs" ]]; then
		return 0
	fi

	echo "--- QML Unit Tests ---"
	for runner in $qmlTestDirs; do
		bash "$runner"
	done
	echo ""
}

_run_qmllint_checks() {
	local qtDeclarativePath
	qtDeclarativePath="${QT_DECLARATIVE_PATH:-$(nix eval nixpkgs#qt6.qtdeclarative.outPath 2>/dev/null | tr -d '"')}"
	local qmllintBin="$qtDeclarativePath/bin/qmllint"

	if [[ ! -x "$qmllintBin" ]]; then
		echo "SKIP: qmllint not found" >&2
		return 0
	fi

	if ! command -v quickshell &>/dev/null; then
		echo "SKIP: quickshell not installed, skipping QML lint" >&2
		return 0
	fi

	local quickshellQmlPath
	quickshellQmlPath="$(nix-store -qR "$(which quickshell)" 2>/dev/null | grep 'quickshell-wrapped-[0-9]' | head -1)/lib/qt-6/qml"
	local qt5compatPath
	qt5compatPath="$(nix eval nixpkgs#qt6Packages.qt5compat.outPath 2>/dev/null | tr -d '"')/lib/qt-6/qml"

	echo "--- QML Lint ---"
	local qmlFiles
	qmlFiles=$(find "$REPO_DIR/.config/quickshell" -name "*.qml" -type f | sort)
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
}
