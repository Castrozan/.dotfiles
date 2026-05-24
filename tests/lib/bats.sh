#!/usr/bin/env bash

_collect_quick_bats_test_files() {
	find "$REPO_DIR/home/base" "$REPO_DIR/home/linux" "$REPO_DIR/home/darwin" -path "*/tests/*.bats" \
		! -name "*-docker.bats" \
		! -name "runtime.bats" \
		! -name "*-runtime.bats" \
		! -name "live-services.bats" \
		! -name "cdp-browser.bats" \
		-type f | sort
}

_run_quick_bats_tests() {
	if ! command -v bats &>/dev/null; then
		echo "WARN: bats not installed, skipping bin script tests" >&2
		echo "      Install with: nix shell nixpkgs#bats" >&2
		return 0
	fi

	echo "--- Bin Script Tests (quick) ---"
	local testFiles
	testFiles=$(_collect_quick_bats_test_files)
	bats $testFiles
	echo ""
}

_run_quick_bats_tests_ci() {
	if ! command -v bats &>/dev/null; then
		echo "SKIP: bats not installed"
		return 0
	fi

	echo "--- Bin Script Tests (ci) ---"
	local testFiles
	testFiles=$(_collect_quick_bats_test_files)
	bats $testFiles
	echo ""
}

_run_bats_with_coverage() {
	if ! command -v kcov &>/dev/null || ! command -v bats &>/dev/null; then
		echo "WARN: kcov or bats not installed, skipping coverage" >&2
		echo "      Install with: nix shell nixpkgs#kcov nixpkgs#bats" >&2
		return 0
	fi

	echo "--- Bin Script Tests with Coverage ---"
	"$SCRIPT_DIR/cover/bash-coverage.sh"
	echo ""
}

_is_runtime_test_file() {
	local filename
	filename="$(basename "$1")"
	[[ "$filename" == "runtime.bats" || "$filename" == *"-runtime.bats" || "$filename" == "live-services.bats" ]]
}

_run_domain_runtime_tests() {
	if ! command -v bats &>/dev/null; then
		echo "WARN: bats not installed, skipping domain runtime tests" >&2
		return 0
	fi

	local runtimeTestFiles=()
	for testFile in "$REPO_DIR"/home/base/*/tests/*.bats "$REPO_DIR"/home/linux/*/tests/*.bats "$REPO_DIR"/home/darwin/*/tests/*.bats; do
		[[ -f "$testFile" ]] || continue
		_is_runtime_test_file "$testFile" || continue
		runtimeTestFiles+=("$testFile")
	done

	if [[ ${#runtimeTestFiles[@]} -eq 0 ]]; then
		echo "No domain runtime test files found"
		return 0
	fi

	echo "--- Domain Runtime Tests (home/{base,linux,darwin}/*/tests/) ---"
	bats "${runtimeTestFiles[@]}"
	echo ""
}
