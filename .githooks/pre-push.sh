#!/usr/bin/env bash

set -Eeuo pipefail

[ "${SKIP_HOOKS:-0}" = "1" ] && exit 0

readonly REPO_ROOT=$(git rev-parse --show-toplevel)

[[ "$(basename "$REPO_ROOT")" != ".dotfiles" ]] && exit 0

cd "$REPO_ROOT"

main() {
	_run_check "statix" nix run nixpkgs#statix -- check . --ignore 'result*'
	_run_check "deadnix" nix run nixpkgs#deadnix -- .
	_run_check "nixfmt" bash -c "find . -name '*.nix' -not -path './result*' -not -path './.worktrees/*' -exec nix run nixpkgs#nixfmt-rfc-style -- --check {} +"
	_run_check "validate-skill-frontmatter" ./agents/evals/validate-skill-frontmatter.sh agents/skills
	_run_quick_bats_tests
	_run_quick_pytest_tests
	_remind_nix_tests_if_openclaw_changed

	echo "All pre-push checks passed."
}

_run_check() {
	local checkName="$1"
	shift
	echo "==> $checkName"
	"$@"
	echo ""
}

_run_quick_bats_tests() {
	echo "==> bats (quick)"
	local testFiles
	testFiles=$(find home/modules -path "*/tests/*.bats" \
		! -name "*-docker.bats" \
		! -name "runtime.bats" \
		! -name "live-services.bats" \
		! -name "cdp-browser.bats" \
		-type f | sort)
	nix shell nixpkgs#bats --command bats $testFiles
	echo ""
}

_run_quick_pytest_tests() {
	if ! command -v pytest &>/dev/null; then
		return 0
	fi

	local testFiles
	testFiles=$(find home/modules agents/hooks -path "*/tests/test_*.py" -type f 2>/dev/null | sort)
	if [[ -z "$testFiles" ]]; then
		return 0
	fi

	echo "==> pytest (quick)"
	pytest $testFiles -x -q
	echo ""
}

_remind_nix_tests_if_openclaw_changed() {
	if _openclaw_files_changed; then
		echo ""
		echo "NOTE: OpenClaw files changed. Run 'nix flake check' to verify nix eval tests."
		echo ""
	fi
}

_openclaw_files_changed() {
	local watchedPaths=(
		"home/modules/openclaw"
		"users/zanoni/home/openclaw"
		"users/lucas.zanoni/home/openclaw"
		"tests/openclaw"
	)

	local changedFiles
	changedFiles=$(git diff --name-only origin/main...HEAD 2>/dev/null || true)

	for watchedPath in "${watchedPaths[@]}"; do
		if echo "$changedFiles" | grep -q "^$watchedPath"; then
			return 0
		fi
	done

	return 1
}

main "$@"
