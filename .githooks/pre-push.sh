#!/usr/bin/env bash

set -Eeuo pipefail

[ "${SKIP_HOOKS:-0}" = "1" ] && exit 0

readonly REPO_ROOT=$(git rev-parse --show-toplevel)

[[ "$(basename "$REPO_ROOT")" != ".dotfiles" ]] && exit 0

cd "$REPO_ROOT"

main() {
  _update_changelog
  _run_check "statix" nix run nixpkgs#statix -- check . --ignore 'result*'
  _run_check "deadnix" nix run nixpkgs#deadnix -- .
  _run_check "nixfmt" bash -c "find . -name '*.nix' -not -path './result*' -not -path './.worktrees/*' -exec nix run nixpkgs#nixfmt-rfc-style -- --check {} +"
  _run_check "validate-agents" ./tests/validate-agents.sh agents/skills
  _run_check "bats" nix shell nixpkgs#bats --command bats tests/scripts/
  _run_openclaw_eval_if_changed

  echo "All pre-push checks passed."
}

_run_check() {
  local checkName="$1"
  shift
  echo "==> $checkName"
  "$@"
  echo ""
}

_update_changelog() {
  echo "==> changelog"
  if nix run nixpkgs#git-cliff -- --output CHANGELOG.md 2>/dev/null; then
    if ! git diff --quiet CHANGELOG.md 2>/dev/null; then
      git add CHANGELOG.md
      git commit -m "chore: update changelog"
    fi
  fi
  echo ""
}

_run_openclaw_eval_if_changed() {
  if _openclaw_files_changed; then
    _run_check "openclaw-eval" \
      nix shell nixpkgs#bats --command bats tests/openclaw/eval.bats
  else
    echo "==> openclaw-eval (skipped — no openclaw changes)"
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
