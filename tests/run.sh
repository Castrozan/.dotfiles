#!/usr/bin/env bash

set -Eeuo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

main() {
	local selectedMode="quick"

	_parse_arguments "$@"

	echo "=== Running Tests (${selectedMode}) ==="
	echo ""

	case "$selectedMode" in
	quick) _run_quick_tier ;;
	nix)
		_run_quick_tier
		_run_nix_tier
		;;
	docker) _run_docker_tier ;;
	runtime) _run_runtime_tier ;;
	all)
		_run_quick_tier
		_run_nix_tier
		_run_docker_tier
		;;
	evals) _run_evals_tier ;;
	perf) _run_perf_tier ;;
	coverage) _run_coverage_tier ;;
	ci) _run_ci_tier ;;
	esac

	echo "=== All Tests Complete ==="
}

_parse_arguments() {
	while [[ $# -gt 0 ]]; do
		case $1 in
		--quick)
			selectedMode="quick"
			shift
			;;
		--nix)
			selectedMode="nix"
			shift
			;;
		--docker)
			selectedMode="docker"
			shift
			;;
		--runtime)
			selectedMode="runtime"
			shift
			;;
		--all)
			selectedMode="all"
			shift
			;;
		--coverage)
			selectedMode="coverage"
			shift
			;;
		--evals)
			selectedMode="evals"
			shift
			;;
		--ci)
			selectedMode="ci"
			shift
			;;
		--perf)
			selectedMode="perf"
			shift
			;;
		*)
			echo "Unknown option: $1" >&2
			exit 1
			;;
		esac
	done
}

_run_quick_tier() {
	_run_skill_frontmatter_validation
	_run_quick_bats_tests
	_run_quick_pytest_tests
	_run_qml_unit_tests
	_run_qmllint_checks
}

_run_nix_tier() {
	_run_nix_flake_checks
}

_run_docker_tier() {
	_run_docker_integration_tests
}

_run_runtime_tier() {
	_run_domain_runtime_tests
}

_run_coverage_tier() {
	_run_skill_frontmatter_validation
	_run_bats_with_coverage
}

_run_ci_tier() {
	_run_skill_frontmatter_validation
	_run_quick_bats_tests_ci
	_run_nix_tier
	_run_rebuild_baseline_check
	_run_desktop_baseline_check
}

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
	local perfTests
	perfTests=$(find "$REPO_DIR/home/modules" -name "perf-runtime.bats" -type f 2>/dev/null | sort)
	if [[ -n "$perfTests" ]] && command -v bats &>/dev/null; then
		bats $perfTests
	else
		echo "SKIP: no perf-runtime.bats files or bats not installed" >&2
	fi
	echo ""
}

_run_evals_tier() {
	if ! command -v claude &>/dev/null; then
		echo "SKIP: claude CLI not installed, skipping agent evals" >&2
		return 0
	fi

	echo "--- Agent Evals (LLM) ---"
	"$REPO_DIR/agents/evals/run-evals.py"
	echo ""
}

_collect_quick_pytest_test_files() {
	find "$REPO_DIR/home/modules" "$REPO_DIR/agents/hooks" "$REPO_DIR/agents/skills" -path "*/tests/test_*.py" -type f | sort
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

_run_skill_frontmatter_validation() {
	echo "--- Skill Frontmatter Validation ---"
	"$REPO_DIR/agents/evals/validate-skill-frontmatter.sh" "$REPO_DIR/agents/skills"
	echo ""
}

_collect_quick_bats_test_files() {
	find "$REPO_DIR/home/modules" -path "*/tests/*.bats" \
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

_detect_current_system() {
	local arch
	arch="$(uname -m)"

	if [[ "$arch" == "arm64" ]]; then
		arch="aarch64"
	fi

	echo "${arch}-linux"
}

_run_nix_flake_checks() {
	if ! command -v nix &>/dev/null; then
		echo "WARN: nix not installed, skipping nix flake checks" >&2
		return 0
	fi

	local currentSystem
	currentSystem="$(_detect_current_system)"

	echo "--- Nix Flake Checks (${currentSystem}) ---"
	local checkNames
	checkNames=$(nix eval ".#checks.${currentSystem}" --apply 'builtins.attrNames' --json 2>/dev/null | jq -r '.[]')
	local failedChecks=0
	for checkName in $checkNames; do
		if nix build ".#checks.${currentSystem}.${checkName}" --no-link --print-build-logs 2>&1; then
			echo "  PASS: ${checkName}"
		else
			echo "  FAIL: ${checkName}"
			failedChecks=$((failedChecks + 1))
		fi
	done
	if [[ "$failedChecks" -gt 0 ]]; then
		echo "FAILED: ${failedChecks} check(s) failed"
		return 1
	fi
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
	for testFile in "$REPO_DIR"/home/modules/*/tests/*.bats; do
		[[ -f "$testFile" ]] || continue
		_is_runtime_test_file "$testFile" || continue
		runtimeTestFiles+=("$testFile")
	done

	if [[ ${#runtimeTestFiles[@]} -eq 0 ]]; then
		echo "No domain runtime test files found"
		return 0
	fi

	echo "--- Domain Runtime Tests (home/modules/*/tests/) ---"
	bats "${runtimeTestFiles[@]}"
	echo ""
}

_run_docker_integration_tests() {
	if ! command -v docker &>/dev/null; then
		echo "WARN: docker not installed, skipping docker integration tests" >&2
		return 0
	fi
	if ! command -v bats &>/dev/null; then
		echo "WARN: bats not installed, skipping docker integration tests" >&2
		return 0
	fi

	echo "--- Docker Integration Tests ---"
	local dockerTestFiles
	dockerTestFiles=$(find "$REPO_DIR/home/modules" -path "*/tests/*-docker.bats" -type f | sort)

	if [[ -z "$dockerTestFiles" ]]; then
		echo "No docker test files found"
		return 0
	fi

	bats $dockerTestFiles
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

_run_qml_unit_tests() {
	local qmlTestDirs
	qmlTestDirs=$(find "$REPO_DIR/home/modules" -path "*/tests/qml/run-qml-tests.sh" -type f | sort)

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

	local quickshellQmlPath
	quickshellQmlPath="$(nix-store -qR "$(which quickshell 2>/dev/null)" 2>/dev/null | grep 'quickshell-[0-9]' | head -1)/lib/qt-6/qml"
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

main "$@"
