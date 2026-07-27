#!/usr/bin/env bash

if [ "${BASH_VERSINFO[0]:-0}" -lt 4 ]; then
	for _candidateBash in \
		/run/current-system/sw/bin/bash \
		"/etc/profiles/per-user/${USER}/bin/bash" \
		/opt/homebrew/bin/bash; do
		if [ -x "$_candidateBash" ]; then
			exec "$_candidateBash" "$0" "$@"
		fi
	done
	echo "__tests__/run.sh: bash >= 4 required, only $BASH_VERSION found" >&2
	exit 1
fi

set -Eeuo pipefail

if [ -z "${__NIX_MEMORY_SCOPED:-}" ] &&
	command -v systemd-run >/dev/null 2>&1 &&
	[ -n "${DBUS_SESSION_BUS_ADDRESS:-}" ]; then
	exec systemd-run --user --scope -q \
		--setenv=__NIX_MEMORY_SCOPED=1 \
		-p MemoryHigh="${DOTFILES_TEST_MEMORY_HIGH:-45%}" \
		-p MemoryMax="${DOTFILES_TEST_MEMORY_MAX:-55%}" \
		-p MemorySwapMax="${DOTFILES_TEST_MEMORY_SWAP_MAX:-0}" \
		-- "$0" "$@"
fi

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# shellcheck source=lib/discovery.sh
source "$SCRIPT_DIR/lib/discovery.sh"
# shellcheck source=lib/bats.sh
source "$SCRIPT_DIR/lib/bats.sh"
# shellcheck source=lib/pytest.sh
source "$SCRIPT_DIR/lib/pytest.sh"
# shellcheck source=lib/nix-checks.sh
source "$SCRIPT_DIR/lib/nix-checks.sh"
# shellcheck source=lib/qml.sh
source "$SCRIPT_DIR/lib/qml.sh"
# shellcheck source=lib/lua.sh
source "$SCRIPT_DIR/lib/lua.sh"
# shellcheck source=lib/line-counts.sh
source "$SCRIPT_DIR/lib/line-counts.sh"
# shellcheck source=lib/evals.sh
source "$SCRIPT_DIR/lib/evals.sh"
# shellcheck source=lib/perf.sh
source "$SCRIPT_DIR/lib/perf.sh"
# shellcheck source=lib/failure-aggregation.sh
source "$SCRIPT_DIR/lib/failure-aggregation.sh"

readonly QUICK_TIER_CHECKS=(
	_run_line_count_check
	_run_quick_bats_tests
	_run_quick_pytest_tests
	_run_qml_unit_tests
	_run_qmllint_checks
	_run_lua_unit_tests
)

readonly NIX_TIER_CHECKS=(
	_run_nix_flake_checks
)

readonly INTEGRATION_SCRIPTS_TIER_CHECKS=(
	_run_integration_scripts_bats_tests
	_run_integration_scripts_pytest_tests
)

readonly RUNTIME_TIER_CHECKS=(
	_run_e2e_scripts_bats_tests
	_run_e2e_scripts_pytest_tests
)

readonly CI_TIER_CHECKS=(
	_run_line_count_check
	_run_quick_bats_tests_ci
	_run_nix_flake_checks
	_run_rebuild_baseline_check
	_run_desktop_baseline_check
)

main() {
	local selectedMode="quick"

	_parse_arguments "$@"

	if [[ "$selectedMode" == "map" ]]; then
		python3 "$SCRIPT_DIR/map-test-suite.py"
		return
	fi

	echo "=== Running Tests (${selectedMode}) ==="
	echo ""

	case "$selectedMode" in
	quick) _run_quick_tier ;;
	nix)
		_run_checks_reporting_every_failure \
			"${QUICK_TIER_CHECKS[@]}" \
			"${NIX_TIER_CHECKS[@]}"
		;;
	integration-scripts) _run_integration_scripts_tier ;;
	runtime) _run_runtime_tier ;;
	all)
		_run_checks_reporting_every_failure \
			"${QUICK_TIER_CHECKS[@]}" \
			"${NIX_TIER_CHECKS[@]}" \
			"${INTEGRATION_SCRIPTS_TIER_CHECKS[@]}"
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
		--integration-scripts | --docker) selectedMode="integration-scripts" && shift ;;
		--runtime) selectedMode="runtime" && shift ;;
		--all) selectedMode="all" && shift ;;
		--coverage) selectedMode="coverage" && shift ;;
		--evals) selectedMode="evals" && shift ;;
		--integration) selectedMode="integration" && shift ;;
		--e2e) selectedMode="e2e" && shift ;;
		--ci) selectedMode="ci" && shift ;;
		--perf) selectedMode="perf" && shift ;;
		--map) selectedMode="map" && shift ;;
		*)
			echo "Unknown option: $1" >&2
			exit 1
			;;
		esac
	done
}

_run_quick_tier() {
	_run_checks_reporting_every_failure "${QUICK_TIER_CHECKS[@]}"
}

_run_nix_tier() {
	_run_checks_reporting_every_failure "${NIX_TIER_CHECKS[@]}"
}

_run_integration_scripts_tier() {
	_run_checks_reporting_every_failure "${INTEGRATION_SCRIPTS_TIER_CHECKS[@]}"
}

_run_runtime_tier() {
	_run_checks_reporting_every_failure "${RUNTIME_TIER_CHECKS[@]}"
}

_run_coverage_tier() {
	_run_bats_with_coverage
}

_run_ci_tier() {
	_run_checks_reporting_every_failure "${CI_TIER_CHECKS[@]}"
}

main "$@"
