#!/usr/bin/env bash

set -euo pipefail

[ "${SKIP_HOOKS:-0}" = "1" ] && exit 0

REPO_ROOT=$(git rev-parse --show-toplevel)

[[ "$(basename "$REPO_ROOT")" != ".dotfiles" ]] && exit 0

cd "$REPO_ROOT"

run_check() {
  local checkName="$1"
  shift
  echo "==> $checkName"
  "$@"
  echo ""
}

echo "==> changelog"
if nix run nixpkgs#git-cliff -- --output CHANGELOG.md 2>/dev/null; then
  if ! git diff --quiet CHANGELOG.md 2>/dev/null; then
    git add CHANGELOG.md
    git commit -m "chore: update changelog"
  fi
fi
echo ""

run_check "statix" \
  nix run nixpkgs#statix -- check . --ignore 'result*'

run_check "deadnix" \
  nix run nixpkgs#deadnix -- .

run_check "nixfmt" \
  bash -c "find . -name '*.nix' -not -path './result*' -not -path './.worktrees/*' -exec nix run nixpkgs#nixfmt-rfc-style -- --check {} +"

run_check "validate-agents" \
  ./tests/validate-agents.sh agents/skills

run_check "bats" \
  nix shell nixpkgs#bats --command bats tests/scripts/

openclawChangedPaths="home/modules/openclaw users/zanoni/home/openclaw users/lucas.zanoni/home/openclaw tests/openclaw"
openclawFilesChanged=false
for changedPath in $openclawChangedPaths; do
  if git diff --name-only origin/main...HEAD | grep -q "^$changedPath"; then
    openclawFilesChanged=true
    break
  fi
done

if [ "$openclawFilesChanged" = true ]; then
  run_check "openclaw-eval" \
    nix shell nixpkgs#bats --command bats tests/openclaw/eval.bats
else
  echo "==> openclaw-eval (skipped — no openclaw changes)"
  echo ""
fi

echo "All pre-push checks passed."
