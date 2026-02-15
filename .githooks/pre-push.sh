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
  _run_check "validate-skill-frontmatter" ./tests/validate-skill-frontmatter.sh agents/skills
  _run_quick_bats_tests
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
  local testFiles=()
  for testFile in tests/bin-scripts/*.bats; do
    [[ "$(basename "$testFile")" == *-docker.bats ]] && continue
    testFiles+=("$testFile")
  done
  nix shell nixpkgs#bats --command bats "${testFiles[@]}"
  echo ""
}

_remind_nix_tests_if_openclaw_changed() {
  if _openclaw_files_changed; then
    echo ""
    echo "NOTE: OpenClaw files changed. Run 'tests/run-all.sh --nix' to verify nix eval tests."
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
