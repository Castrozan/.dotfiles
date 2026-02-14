#!/usr/bin/env bash

set -Eeuo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

main() {
  local ciMode=false
  local coverageMode=false
  local runtimeMode=false

  _parse_arguments "$@"

  echo "=== Running Tests ==="
  echo ""

  _run_skill_validation
  _run_script_tests
  _run_module_eval_tests
  _run_openclaw_eval_tests
  _run_openclaw_runtime_tests

  echo "=== All Tests Complete ==="
}

_parse_arguments() {
  while [[ $# -gt 0 ]]; do
    case $1 in
      --ci) ciMode=true; shift ;;
      --coverage) coverageMode=true; shift ;;
      --runtime) runtimeMode=true; shift ;;
      *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
  done
}

_run_skill_validation() {
  echo "--- Skill Validation ---"
  "$SCRIPT_DIR/validate-agents.sh" "$SCRIPT_DIR/../agents/skills"
  echo ""
}

_run_script_tests() {
  if [[ "$coverageMode" == "true" ]]; then
    _run_script_tests_with_coverage
  elif command -v bats &>/dev/null; then
    echo "--- Script Tests (bats) ---"
    bats "$SCRIPT_DIR/scripts/"
  elif [[ "$ciMode" == "true" ]]; then
    echo "SKIP: bats not installed"
  else
    echo "WARN: bats not installed, skipping script tests"
    echo "      Install with: nix shell nixpkgs#bats"
  fi
}

_run_script_tests_with_coverage() {
  if command -v kcov &>/dev/null && command -v bats &>/dev/null; then
    echo "--- Script Tests with Coverage ---"
    "$SCRIPT_DIR/coverage.sh"
  else
    echo "WARN: kcov or bats not installed, skipping coverage"
    echo "      Install with: nix shell nixpkgs#kcov nixpkgs#bats"
  fi
}

_run_module_eval_tests() {
  if command -v nix &>/dev/null && command -v bats &>/dev/null; then
    echo "--- Module Evaluation Tests (bats + nix eval) ---"
    bats "$SCRIPT_DIR/modules/eval.bats"
  elif [[ "$ciMode" == "true" ]]; then
    echo "SKIP: nix or bats not installed for module eval tests"
  else
    echo "WARN: nix or bats not installed, skipping module eval tests"
  fi
  echo ""
}

_run_openclaw_eval_tests() {
  if command -v nix &>/dev/null && command -v bats &>/dev/null; then
    echo "--- OpenClaw Evaluation Tests (bats + nix eval) ---"
    bats "$SCRIPT_DIR/openclaw/eval.bats"
  elif [[ "$ciMode" == "true" ]]; then
    echo "SKIP: nix or bats not installed for openclaw eval tests"
  else
    echo "WARN: nix or bats not installed, skipping openclaw eval tests"
  fi
  echo ""
}

_run_openclaw_runtime_tests() {
  [[ "$runtimeMode" != "true" ]] && return 0

  if command -v bats &>/dev/null; then
    echo "--- OpenClaw Runtime Tests (bats) ---"
    bats "$SCRIPT_DIR/openclaw/runtime.bats"
  else
    echo "WARN: bats not installed, skipping runtime tests"
  fi
  echo ""
}

main "$@"
