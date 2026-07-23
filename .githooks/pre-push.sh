#!/usr/bin/env bash

set -Eeuo pipefail

[ "${SKIP_HOOKS:-0}" = "1" ] && exit 0

REPO_ROOT=$(git rev-parse --show-toplevel)
readonly REPO_ROOT

[[ "$(basename "$REPO_ROOT")" != ".dotfiles" ]] && exit 0

cd "$REPO_ROOT"

main() {
	_run_check "statix" nix run nixpkgs#statix -- check . --ignore 'result*'
	_run_check "deadnix" nix run nixpkgs#deadnix -- .
	_run_check "nixfmt" bash -c "find . -name '*.nix' -not -path './result*' -not -path './.worktrees/*' -exec nix run nixpkgs#nixfmt-rfc-style -- --check {} +"
	_run_check "quick tests" ./__tests__/run.sh --quick

	echo "All pre-push checks passed."
}

_run_check() {
	local checkName="$1"
	shift
	echo "==> $checkName"
	"$@"
	echo ""
}

main "$@"
