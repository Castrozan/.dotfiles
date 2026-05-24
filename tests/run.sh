#!/usr/bin/env bash

set -Eeuo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# shellcheck source=lib/bats.sh
source "$SCRIPT_DIR/lib/bats.sh"
# shellcheck source=lib/pytest.sh
source "$SCRIPT_DIR/lib/pytest.sh"
# shellcheck source=lib/nix-checks.sh
source "$SCRIPT_DIR/lib/nix-checks.sh"
# shellcheck source=lib/docker.sh
source "$SCRIPT_DIR/lib/docker.sh"
# shellcheck source=lib/qml.sh
source "$SCRIPT_DIR/lib/qml.sh"
# shellcheck source=lib/skill-frontmatter.sh
source "$SCRIPT_DIR/lib/skill-frontmatter.sh"
# shellcheck source=lib/evals.sh
source "$SCRIPT_DIR/lib/evals.sh"
# shellcheck source=lib/perf.sh
source "$SCRIPT_DIR/lib/perf.sh"

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
	integration) _run_integration_tier ;;
	e2e) _run_e2e_tier ;;
	perf) _run_perf_tier ;;
	coverage) _run_coverage_tier ;;
	ci) _run_ci_tier ;;
	esac

	echo "=== All Tests Complete ==="
}

_parse_arguments() {
	while [[ $# -gt 0 ]]; do
		case $1 in
		--quick) selectedMode="quick" && shift ;;
		--nix) selectedMode="nix" && shift ;;
		--docker) selectedMode="docker" && shift ;;
		--runtime) selectedMode="runtime" && shift ;;
		--all) selectedMode="all" && shift ;;
		--coverage) selectedMode="coverage" && shift ;;
		--evals) selectedMode="evals" && shift ;;
		--integration) selectedMode="integration" && shift ;;
		--e2e) selectedMode="e2e" && shift ;;
		--ci) selectedMode="ci" && shift ;;
		--perf) selectedMode="perf" && shift ;;
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

main "$@"
