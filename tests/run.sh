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
	find "$REPO_DIR/home/modules" -path "*/tests/test_*.py" -type f | sort
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
		! -name "live-services.bats" \
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

_run_nix_flake_checks() {
	if ! command -v nix &>/dev/null; then
		echo "WARN: nix not installed, skipping nix flake checks" >&2
		return 0
	fi

	echo "--- Nix Flake Checks ---"
	nix flake check --print-build-logs 2>&1
	echo ""
}

_is_runtime_test_file() {
	local filename
	filename="$(basename "$1")"
	[[ "$filename" == "runtime.bats" || "$filename" == "live-services.bats" ]]
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

main "$@"
